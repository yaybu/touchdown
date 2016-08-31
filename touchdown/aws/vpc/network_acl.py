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
from touchdown.aws.common import Resource, TagsMixin
from touchdown.core import argument, serializers
from touchdown.core.plan import Plan

from ..replacement import (
    ReplacementApply,
    ReplacementDescribe,
    ReplacementDestroy,
)
from .vpc import VPC


class PortRange(Resource):

    resource_name = 'port_range'

    start = argument.Integer(default=1, min=1, max=65535, field='From')
    end = argument.Integer(default=65535, min=1, max=65535, field='To')

    @classmethod
    def clean(cls, value):
        if value == '*':
            return super(PortRange, cls).clean({'start': 1, 'end': 65535})
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                pass
        if isinstance(value, int):
            return super(PortRange, cls).clean({'start': value, 'end': value})
        return super(PortRange, cls).clean(value)


class IcmpTypeCode(Resource):

    resource_name = 'icmp_type_code'

    type = argument.Integer(default=-1, field='Type')
    code = argument.Integer(default=-1, field='Code')


class Rule(Resource):

    resource_name = 'rule'
    dot_ignore = True

    network = argument.IPNetwork(field='CidrBlock')
    protocol = argument.String(default='tcp', choices=['tcp', 'udp', 'icmp'], field='Protocol')
    port = argument.Resource(PortRange, field='PortRange', serializer=serializers.Resource())
    icmp = argument.Resource(IcmpTypeCode, field='IcmpTypeCode', serializer=serializers.Resource())
    action = argument.String(default='allow', choices=['allow', 'deny'], field='RuleAction')

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
        rule = []

        if self.network:
            rule.append('network={}'.format(str(self.network)))

        if self.protocol:
            rule.append('protocol={}'.format({
                '6': 'tcp',
                '17': 'udp',
                '1': 'icmp',
                '-1': 'all',
            }.get(self.protocol, self.protocol)))

        if self.port:
            if self.port.start == self.port.end:
                rule.append('port={}'.format(self.port.start))
            else:
                if self.port.start:
                    rule.append('port__start={}'.format(self.port.start))
                if self.port.end:
                    rule.append('port__end={}'.format(self.port.end))

        if self.icmp:
            if self.icmp.type:
                rule.append('icmp__type={}'.format(self.icmp.type))
            if self.icmp.code:
                rule.append('icmp__code={}'.format(self.icmp.code))

        if self.action:
            rule.append('action={}'.format(self.action))

        return 'rule({})'.format(', '.join(rule))


class NetworkACL(Resource):

    resource_name = 'network_acl'

    name = argument.String(field='Name', group='tags')
    inbound = argument.ResourceList(Rule)
    outbound = argument.ResourceList(Rule)

    tags = argument.Dict()
    vpc = argument.Resource(VPC, field='VpcId')


class Describe(ReplacementDescribe, Plan):

    resource = NetworkACL
    service_name = 'ec2'
    api_version = '2015-10-01'
    describe_action = 'describe_network_acls'
    describe_envelope = 'NetworkAcls'
    key = 'NetworkAclId'

    biggest_serial = 0

    def get_describe_filters(self):
        vpc = self.runner.get_plan(self.resource.vpc)
        if not vpc.resource_id:
            return None

        return {
            'Filters': [
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
        super(Describe, self).describe_object_matches(network_acl)
        return self._compare_rules(network_acl)

    def name_for_remote(self, network_acl):
        tags = {tag['Key']: tag['Value'] for tag in network_acl.get('Tags', [])}
        return tags.get('Name', '')

    def is_possible_object(self, obj):
        if obj['IsDefault']:
            return False
        return super(Describe, self).is_possible_object(obj)


class Apply(TagsMixin, ReplacementApply, Describe):

    create_action = 'create_network_acl'
    waiter = 'network_acl_available'
    waiter_eventual_consistency_threshold = 5
    destroy_action = 'delete_network_acl'

    def get_create_serializer(self):
        return serializers.Resource()

    def is_stale(self, network_acl):
        if len(network_acl['Associations']) > 0:
            return False
        return super(Apply, self).is_stale(network_acl)

    def _insert_rule(self, rule, rule_number, egress):
        return self.generic_action(
            'Add {direction} rule: {rule}'.format(
                rule=rule,
                direction='egress' if egress else 'ingress',
            ),
            self.client.create_network_acl_entry,
            rule.serializer_with_kwargs(
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


class Destroy(ReplacementDestroy, Describe):

    destroy_action = 'delete_network_acl'
