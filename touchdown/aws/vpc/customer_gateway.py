# Copyright 2015 Isotoma Limited
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

from touchdown.core import argument
from touchdown.core.plan import Plan, Present
from touchdown.core.resource import Resource

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy, TagsMixin


class CustomerGateway(Resource):

    resource_name = 'customer_gateway'

    name = argument.String(field='Name', group='tags')
    type = argument.String(default='ipsec.1', choices=['ipsec.1'], field='Type')
    public_ip = argument.IPAddress(field='PublicIp')
    bgp_asn = argument.Integer(default=65000, field='BgpAsn')
    tags = argument.Dict()
    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = CustomerGateway
    service_name = 'ec2'
    api_version = '2015-10-01'
    describe_action = 'describe_customer_gateways'
    describe_envelope = 'CustomerGateways'
    key = 'CustomerGatewayId'

    def get_describe_filters(self):
        return {
            'Filters': [
                {'Name': 'tag:Name', 'Values': [self.resource.name]},
            ],
        }


class Apply(TagsMixin, SimpleApply, Describe):

    create_action = 'create_customer_gateway'
    waiter = 'customer_gateway_available'

    signature = (
        Present('name'),
        Present('public_ip'),
    )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_customer_gateway'
