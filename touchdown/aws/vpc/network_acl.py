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

from touchdown.core.resource import Resource
from touchdown.core.plan import Plan
from touchdown.core import argument

from .vpc import VPC
from touchdown.core import serializers
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy


class Rule(Resource):

    resource_name = "rule"
    dot_ignore = True

    network = argument.IPNetwork(field="CidrBlock")
    protocol = argument.String(default='tcp', choices=['tcp', 'udp', 'icmp'], field="Protocol")
    port = argument.Integer(min=-1, max=65535)
    from_port = argument.Integer(default=lambda r: r.port if r.port != -1 else 1, min=-1, max=65535)
    to_port = argument.Integer(default=lambda r: r.port if r.port != -1 else 65535, min=-1, max=65535)
    action = argument.String(default="allow", choices=["allow", "deny"], field="RuleAction")

    extra_serializers = {
        "PortRange": serializers.Dict(
            From=serializers.Integer(serializers.Argument("from_port")),
            To=serializers.Integer(serializers.Argument("to_port")),
        ),
    }

    def __str__(self):
        name = super(Rule, self).__str__()
        if self.from_port == self.to_port:
            ports = "port {}".format(self.from_port)
        else:
            ports = "ports {} to {}".format(self.from_port, self.to_port)
        return "{}: {} {} from {}".format(name, self.protocol, ports, self.network)


class NetworkACL(Resource):

    resource_name = "network_acl"

    name = argument.String()
    inbound = argument.ResourceList(Rule)
    outbound = argument.ResourceList(Rule)

    tags = argument.Dict()
    vpc = argument.Resource(VPC, field="VpcId")


class Describe(SimpleDescribe, Plan):

    resource = NetworkACL
    service_name = 'ec2'
    describe_action = "describe_network_acls"
    describe_list_key = "NetworkAcls"
    key = 'NetworkAclId'

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
                {'Name': 'tag:Name', 'Values': [self.resource.name]},
                {'Name': 'vpc-id', 'Values': [vpc.resource_id]}
            ],
        }


class Apply(SimpleApply, Describe):

    create_action = "create_network_acl"

    def _fix_protocol(self, protocol):
        # see https://github.com/aws/aws-cli/pull/532/files
        if protocol == 'tcp':
            return '6'
        elif protocol == 'udp':
            return '17'
        elif protocol == 'icmp':
            return '1'
        elif protocol == 'all':
            return '-1'

    def _get_local_rules(self):
        local_rules = {}
        for i, rule in enumerate(self.resource.inbound, start=1):
            rule = serializers.Resource().render(self.runner, rule)
            rule['Protocol'] = self._fix_protocol(rule['Protocol'])
            rule['RuleNumber'] = i
            rule['Egress'] = False
            local_rules[(False, i)] = rule

        for i, rule in enumerate(self.resource.outbound, start=1):
            rule = serializers.Resource().render(self.runner, rule)
            rule['RuleNumber'] = i
            rule['Protocol'] = self._fix_protocol(rule['Protocol'])
            rule['Egress'] = True
            local_rules[(True, i)] = rule
        return local_rules

    def _get_remote_rules(self):
        remote_rules = {}
        for rule in self.object.get("Entries", []):
            if rule['RuleNumber'] > 32766:
                continue
            remote_rules[(rule['Egress'], rule['RuleNumber'])] = rule
        return remote_rules

    def update_object(self):
        for action in super(Apply, self).update_object():
            yield action

        local_rules = self._get_local_rules()
        remote_rules = self._get_remote_rules()

        for key, rule in remote_rules.items():
            if key not in local_rules or local_rules[key] != rule:
                yield self.generic_action(
                    "Remove rule {} ({})".format(rule['RuleNumber'], 'egrees' if rule['Egress'] else 'ingress'),
                    self.client.delete_network_acl_entry,
                    NetworkAclId=serializers.Identifier(),
                    RuleNumber=rule['RuleNumber'],
                    Egress=rule['Egress'],
                )

        for key, rule in local_rules.items():
            if key not in remote_rules or remote_rules[key] != rule:
                if rule['Egress']:
                    description = "Add rule: {0[RuleAction]} egress from {0[CidrBlock]}, port {0[PortRange][From]} to {0[PortRange][To]}".format(rule)
                else:
                    description = "Add rule: {0[RuleAction]} ingress from {0[CidrBlock]}, port {0[PortRange][From]} to {0[PortRange][To]}".format(rule)

                yield self.generic_action(
                    description,
                    self.client.create_network_acl_entry,
                    NetworkAclId=serializers.Identifier(),
                    **rule
                )


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_network_acl"
