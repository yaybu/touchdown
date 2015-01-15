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

    network = argument.IPNetwork(
        field="IpRanges",
        serializer=serializers.ListOfOne(serializers.Dict(
            CidrIp=serializers.String(),
        )),
    )
    protocol = argument.String(default='tcp', choices=['tcp', 'udp', 'icmp'], field="IpProtocol")
    port = argument.Integer(min=-1, max=32768)
    from_port = argument.Integer(default=lambda r: r.port, min=-1, max=32768, field="FromPort")
    to_port = argument.Integer(default=lambda r: r.port, min=-1, max=32768, field="ToPort")
    action = argument.String(default="ALLOW", choices=["ALLOW", "DENY"])

    def __str__(self):
        name = super(Rule, self).__str__()
        if self.from_port == self.to_port:
            ports = "port {}".format(self.from_port)
        else:
            ports = "ports {} to {}".format(self.from_port, self.to_port)
        return "{}: {} {} from {}".format(name, self.protocol, ports, self.network)


class NetworkACL(Resource):

    resource_name = "network_acl"

    name = argument.String(field="GroupName")
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

        return {
            "Filters": [
                {'Name': 'tag:Name', 'Values': [self.resource.name]},
                {'Name': 'vpc-id', 'Values': [vpc.resource_id]}
            ],
        }


class Apply(SimpleApply, Describe):

    create_action = "create_network_acl"

    def _get_local_rules(self):
        local_rules = {}
        for i, rule in enumerate(self.resource.inbound):
            rule = serializers.Resource().render(self.runner, rule)
            rule['RuleNumber'] = i
            local_rules[(False, i)] = rule

        for i, rule in enumerate(self.resource.outbound):
            rule = serializers.Resource().render(self.runner, rule)
            rule['RuleNumber'] = i
            local_rules[(True, i)] = rule
        return local_rules

    def _get_remote_rules(self):
        remote_rules = {}
        for rule in self.object.get("Entries", []):
            remote_rules[(rule['Egress'], rule['RuleNumber'])] = rule
        return remote_rules

    def update_object(self):
        for action in super(Apply, self).update_object():
            yield action

        local_rules = self._get_local_rules()
        remote_rules = self._get_remote_rules()

        for key, rule in local_rules.items():
            if key not in self.remote_rules or self.remote_rules[key] != rule:
                #FIXME: Rule stale or out of date
                print("UPSERT", rule)

        for rule in remote_rules.keys():
            if rule not in local_rules:
                #FIXME: Delete remote rule not present @ local
                print("DELETE", remote_rules[rule])


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_network_acl"
