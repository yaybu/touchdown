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

from touchdown.core import argument, serializers
from touchdown.core.plan import Plan, Present
from touchdown.core.resource import Resource

from ..common import SimpleApply, SimpleDescribe, SimpleDestroy, TagsMixin
from .vpc import VPC


class Rule(Resource):

    resource_name = 'rule'

    @property
    def dot_ignore(self):
        return self.security_group is None

    protocol = argument.String(default='tcp', choices=['tcp', 'udp', 'icmp'], field='IpProtocol')
    port = argument.Integer(min=-1, max=32768)
    from_port = argument.Integer(default=lambda r: r.port, min=-1, max=32768, field='FromPort')
    to_port = argument.Integer(default=lambda r: r.port, min=-1, max=32768, field='ToPort')

    security_group = argument.Resource(
        'touchdown.aws.vpc.security_group.SecurityGroup',
        field='UserIdGroupPairs',
        serializer=serializers.ListOfOne(serializers.Dict(
            UserId=serializers.Property('OwnerId'),
            GroupId=serializers.Identifier(),
        )),
    )

    network = argument.IPNetwork(
        field='IpRanges',
        serializer=serializers.ListOfOne(serializers.Dict(
            CidrIp=serializers.String(),
        )),
    )

    def exists(self, runner):
        if self.security_group:
            # If the SecurityGroup doesn't exist yet then this rule can't exist
            # yet - so we can bail early!
            if not runner.get_plan(self.security_group).resource_id:
                return False
        return True

    def match_security_group(self, runner, rule):
        if self.security_group:
            sg = runner.get_plan(self.security_group)
            if sg and sg.object:
                for group in rule.get('UserIdGroupPairs', []):
                    if group['GroupId'] == sg.resource_id and group['UserId'] == sg.object['OwnerId']:
                        return True
        return False

    def match_network(self, runner, rule):
        if self.network:
            for network in rule.get('IpRanges', []):
                if network['CidrIp'] == str(self.network):
                    return True
        return False

    def matches(self, runner, rule):
        if not self.exists(runner):
            return False

        if self.protocol != rule['IpProtocol']:
            return False
        if self.from_port != rule.get('FromPort', None):
            return False
        if self.to_port != rule.get('ToPort', None):
            return False
        return self.match_security_group(runner, rule) or self.match_network(runner, rule)

    def __str__(self):
        name = super(Rule, self).__str__()
        if self.from_port == self.to_port:
            ports = 'port {}'.format(self.from_port)
        else:
            ports = 'ports {} to {}'.format(self.from_port, self.to_port)
        return '{}: {} {} from {}'.format(name, self.protocol, ports, self.network if self.network else self.security_group)


class SecurityGroup(Resource):

    resource_name = 'security_group'

    name = argument.String(field='GroupName')
    description = argument.String(field='Description')

    ingress = argument.ResourceList(Rule)
    egress = argument.ResourceList(
        Rule,
        default=lambda instance: [dict(protocol=-1, network=['0.0.0.0/0'])],
    )

    tags = argument.Dict()
    vpc = argument.Resource(VPC, field='VpcId')


class Describe(SimpleDescribe, Plan):

    resource = SecurityGroup
    service_name = 'ec2'
    api_version = '2015-10-01'
    describe_action = 'describe_security_groups'
    describe_envelope = 'SecurityGroups'
    key = 'GroupId'

    def get_describe_filters(self):
        vpc = self.runner.get_plan(self.resource.vpc)
        if not vpc.resource_id:
            return None

        vpc = self.runner.get_plan(self.resource.vpc)
        return {
            'Filters': [
                {'Name': 'group-name', 'Values': [self.resource.name]},
                {'Name': 'vpc-id', 'Values': [vpc.resource_id or '']}
            ],
        }


class Apply(TagsMixin, SimpleApply, Describe):

    create_action = 'create_security_group'
    create_response = 'id-only'

    signature = (
        Present('name'),
        Present('description'),
    )

    def update_object(self):
        for local_rule in self.resource.ingress:
            for remote_rule in self.object.get('IpPermissions', []):
                if local_rule.matches(self.runner, remote_rule):
                    break
            else:
                yield self.generic_action(
                    'Authorize ingress {}'.format(local_rule),
                    self.client.authorize_security_group_ingress,
                    GroupId=serializers.Identifier(),
                    IpPermissions=serializers.ListOfOne(local_rule.serializer_with_kwargs()),
                )

        return

        for local_rule in self.resource.egress:
            for remote_rule in self.object.get('IpPermissionsEgress', []):
                if local_rule.matches(self.runner, remote_rule):
                    break
            else:
                yield self.generic_action(
                    'Authorize egress {}'.format(local_rule),
                    self.client.authorize_security_group_egress,
                    GroupId=serializers.Identifier(),
                    IpPermissions=serializers.ListOfOne(local_rule.serializer_with_kwargs()),
                )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_security_group'
