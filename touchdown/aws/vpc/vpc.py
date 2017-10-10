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
from touchdown.core.plan import Plan
from touchdown.core.resource import Resource

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy, TagsMixin


class VPC(Resource):

    resource_name = 'vpc'

    name = argument.String(field='Name', group='tags')
    cidr_block = argument.IPNetwork(field='CidrBlock')
    tenancy = argument.String(default='default', choices=['default', 'dedicated'], field='InstanceTenancy')

    tags = argument.Dict()

    account = argument.Resource(BaseAccount)

    enable_dns_support = argument.Boolean(
        default=True,
        field='EnableDnsSupport',
        serializer=serializers.Dict(
            Value=serializers.Identity()
        ),
        group='dns_support_attribute',
    )

    enable_dns_hostnames = argument.Boolean(
        default=True,
        field='EnableDnsHostnames',
        serializer=serializers.Dict(
            Value=serializers.Identity()
        ),
        group='dns_hostnames_attribute',
    )


class Describe(SimpleDescribe, Plan):

    resource = VPC
    service_name = 'ec2'
    api_version = '2015-10-01'
    describe_action = 'describe_vpcs'
    describe_envelope = 'Vpcs'
    key = 'VpcId'

    def get_describe_filters(self):
        return {
            'Filters': [
                {'Name': 'tag:Name', 'Values': [self.resource.name]},
            ],
        }

    def annotate_object(self, obj):
        obj['EnableDnsSupport'] = self.client.describe_vpc_attribute(
            Attribute='enableDnsSupport',
            VpcId=obj['VpcId'],
        )['EnableDnsSupport']
        obj['EnableDnsHostnames'] = self.client.describe_vpc_attribute(
            Attribute='enableDnsHostnames',
            VpcId=obj['VpcId'],
        )['EnableDnsHostnames']
        return obj


class Apply(TagsMixin, SimpleApply, Describe):

    create_action = 'create_vpc'
    waiter = 'vpc_available'

    def update_dnssupport_attribute(self):
        diff = self.resource.diff(
            self.runner,
            self.object.get('EnableDnsSupport', {}),
            group='dns_support_attribute',
        )
        if not diff.matches():
            yield self.generic_action(
                ['Configure DNS Support Setting'] + list(diff.lines()),
                self.client.modify_vpc_attribute,
                VpcId=serializers.Identifier(),
                EnableDnsSupport=serializers.Argument('enable_dns_support'),
            )

    def update_dnshostnames_attribute(self):
        diff = self.resource.diff(
            self.runner,
            self.object.get('EnableDnsHostnames', {}),
            group='dns_hostnames_attribute',
        )
        if not diff.matches():
            yield self.generic_action(
                ['Configure DNS Hostnames Setting'] + list(diff.lines()),
                self.client.modify_vpc_attribute,
                VpcId=serializers.Identifier(),
                EnableDnsHostnames=serializers.Argument('enable_dns_hostnames'),
            )

    def update_object(self):
        for action in super(Apply, self).update_object():
            yield action
        for action in self.update_dnssupport_attribute():
            yield action
        for action in self.update_dnshostnames_attribute():
            yield action


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_vpc'
    # waiter = 'vpc_terminated'
