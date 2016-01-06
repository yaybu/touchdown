# Copyright 2014 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from six.moves import zip_longest

from touchdown.core.plan import Plan, Present
from touchdown.core import argument

from .vpc import VPC
from touchdown.core import serializers
from touchdown.aws.common import Resource
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy


class PortRange(Resource):

    resource_name = "port_range"

    start = argument.Integer(default=1, min=-1, max=65535, field="From")
    end = argument.Integer(default=65535, min=-1, max=65535, field="To")


class IcmpTypeCode(Resource):

    resource_name = "icmp_type_code"

    type = argument.Integer(default=-1, field="Type")
    code = argument.Integer(default=-1, field="Code")


class Rule(Resource):

    resource_name = "rule"
    dot_ignore = True

    network = argument.IPNetwork(field="CidrBlock")
    protocol = argument.String(default='tcp', choices=['tcp', 'udp', 'icmp'], field="Protocol")
    port = argument.Resource(PortRange, field="PortRange", serializer=serializers.Resource())
    icmp = argument.Resource(IcmpTypeCode, field="IcmpTypeCode", serializer=serializers.Resource())
    action = argument.String(default="allow", choices=["allow", "deny"], field="RuleAction")

    # def clean_port(self, value):
    #     if isinstance(value, (int, str)):
    #         return PortRange(None, from_port=value, to_port=value)
    #     return value

    def clean_protocol(self, protocol):
        # see https://github.com/aws/aws-cli/pull/532/files
        if protocol == 'tcp':
            return '6'
        elif protocol == 'udp':
            return '17'
        elif protocol == 'icmp':
            return '1'
        elif protocol == 'all':
            return '-1'

    def __str__(self):
        # if self.from_port == self.to_port:
        #     ports = "port {}".format(self.from_port)
        # else:
        #     ports = "ports {} to {}".format(self.from_port, self.to_port)
        ports = ""
        return "{} {} from {}".format(self.protocol, ports, self.network)


class NetworkACL(Resource):

    resource_name = "network_acl"

    name = argument.String(field="Name", group="tags")
    inbound = argument.ResourceList(Rule)
    outbound = argument.ResourceList(Rule)

    tags = argument.Dict()
    vpc = argument.Resource(VPC, field="VpcId")


class Describe(SimpleDescribe, Plan):

    resource = NetworkACL
    service_name = 'ec2'
    describe_action = "describe_network_acls"
    describe_envelope = "NetworkAcls"
    key = 'NetworkAclId'

    biggest_serial = 0

    def get_describe_filters(self):
        vpc = self.runner.get_plan(self.resource.vpc)
        if not vpc.resource_id:
            return None

        if self.key in self.object:
            return {
                "Filters": [
                    {'Name': 'network-acl-id', 'Values': [self.object[self.key]]}
                ]
            }

        return {
            "Filters": [
                {'Name': 'vpc-id', 'Values': [vpc.resource_id]}
            ],
        }

    def _check_rules(self, local, remote, egress):
        rules = zip_longest(
            local,
            filter(
                lambda r: r['Egress'] == egress and r['RuleNumber'] <= 32766,
                remote['Entries'],
            ),
        )
        for i, (left, right) in enumerate(rules, start=1):
            if not left or not right:
                return False
            if i != right['RuleNumber']:
                return False
            if not left.matches(self.runner, right):
                return False
        return True

    def _compare_rules(self, network_acl):
        if not self._check_rules(self.resource.inbound, network_acl, False):
            return False
        if not self._check_rules(self.resource.outbound, network_acl, True):
            return False
        return True

    def describe_object_matches(self, network_acl):
        if self.key in self.object and network_acl[self.key] == self.object[self.key]:
            return True

        tags = {tag['Key']: tag['Value'] for tag in network_acl.get("Tags", [])}
        name = tags.get('Name', '')

        if name != self.resource.name and not name.startswith(self.resource.name + "."):
            return False

        try:
            serial = name.rsplit(".", 1)[1]
            self.biggest_serial = max(int(serial), self.biggest_serial)
        except (IndexError, TypeError, ValueError):
            pass

        return self._compare_rules(network_acl)

    def get_possible_objects(self):
        vpc = self.runner.get_plan(self.resource.vpc)
        if not vpc.resource_id:
            return

        prefix = "{}.".format(self.resource.name)

        result = self.client.describe_network_acls(
            Filters=[
                {"Name": 'vpc-id', "Values": [vpc.resource_id]},
            ]
        )

        for network_acl in result.get('NetworkAcls', []):
            tags = {tag['Key']: tag['Value'] for tag in network_acl.get("Tags", [])}
            name = tags.get('Name', '')

            # Only ignore ACL's for the current resource
            if name != self.resource.name and not name.startswith(prefix):
                continue

            # Don't delete the default ACL
            if network_acl['IsDefault']:
                continue

            yield network_acl

    def get_next_available_name(self):
        return "{}.{}".format(
            self.resource.name,
            self.biggest_serial + 1,
        )


class Apply(SimpleApply, Describe):

    create_action = "create_network_acl"
    waiter = "network_acl_available"
    waiter_eventual_consistency_threshold = 5

    def prepare_to_create(self):
        for network_acl in self.get_possible_objects():
            # Don't try and delete ACL's that are in use
            if len(network_acl['Associations']) != 0:
                continue

            yield self.generic_action(
                "Destroy stale network acl: {}".format(network_acl['NetworkAclId']),
                self.client.delete_network_acl,
                NetworkAclId=network_acl['NetworkAclId'],
            )

    def _insert_rule(self, rule, rule_number, egress):
        return self.generic_action(
            "Add {direction} rule: {rule}".format(
                rule=rule,
                direction='egress' if egress else 'ingress',
            ),
            self.client.create_network_acl_entry,
            rule.serializer_with_args(
                NetworkAclId=self.resource.identifier(),
                Egress=egress,
                RuleNumber=rule_number,
            )
        )

    def insert_network_rules(self):
        for i, rule in enumerate(self.resource.inbound, start=1):
            yield self._insert_rule(rule, rule_number=i, egress=False)
        for i, rule in enumerate(self.resource.outbound, start=1):
            yield self._insert_rule(rule, rule_number=i, egress=True)

    def update_object(self):
        for action in super(Apply, self).update_object():
            yield action

        if not self.object:
            for action in self.insert_network_rules():
                yield action


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_network_acl"

    def destroy_object(self):
        for action in super(Destroy, self).destroy_object():
            yield action

        for network_acl in self.get_possible_objects():
            if network_acl['NetworkAclId'] == self.resource_id:
                continue

            yield self.generic_action(
                "Destroy stale network acl: {}".format(network_acl['NetworkAclId']),
                self.client.delete_network_acl,
                NetworkAclId=network_acl['NetworkAclId'],
            )
