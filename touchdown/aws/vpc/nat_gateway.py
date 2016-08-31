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

from touchdown.core import argument, serializers
from touchdown.core.plan import Plan
from touchdown.core.resource import Resource

from ..common import SimpleApply, SimpleDescribe, SimpleDestroy
from .elastic_ip import ElasticIp
from .subnet import Subnet


class NatGateway(Resource):

    resource_name = 'nat_gateway'

    name = argument.Callable(lambda r: r.subnet.name)

    elastic_ip = argument.Resource(
        ElasticIp,
        field='AllocationId',
        serializer=serializers.Property('AllocationId'),
    )

    subnet = argument.Resource(
        Subnet,
        field='SubnetId',
        serializer=serializers.Identifier(),
    )


class Describe(SimpleDescribe, Plan):

    resource = NatGateway
    service_name = 'ec2'
    api_version = '2015-10-01'
    describe_action = 'describe_nat_gateways'
    describe_envelope = 'NatGateways'
    key = 'NatGatewayId'
    signature = ()

    def get_describe_filters(self):
        subnet = self.runner.get_plan(self.resource.subnet)
        if not subnet.resource_id:
            return None

        return {
            'Filters': [
                {'Name': 'subnet-id', 'Values': [subnet.resource_id]},
            ]
        }


class Apply(SimpleApply, Describe):

    create_action = 'create_nat_gateway'
    waiter = 'nat_gateway_available'


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_nat_gateway'
    waiter = 'nat_gateway_deleted'
