# Copyright 2016 Isotoma Limited
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

from touchdown.config import String
from touchdown.core import argument, serializers
from touchdown.core.plan import Plan
from touchdown.core.resource import Resource

from ..common import Action, SimpleApply, SimpleDescribe, SimpleDestroy
from .route_table import RouteTable
from .vpc import VPC


class Endpoint(Resource):

    resource_name = 'endpoint'

    id = argument.Resource(String)
    name = argument.String()
    service = argument.String(
        field='ServiceName',
        choices=['s3'],
    )
    route_tables = argument.ResourceList(RouteTable, field='RouteTableIds')
    policy = argument.String(field='PolicyDocument')
    vpc = argument.Resource(VPC, field='VpcId')


class NameAction(Action):

    @property
    def description(self):
        yield 'Store vpc_endpoint id as setting {!r}'.format(self.resource.id.name)

    def run(self):
        self.runner.get_service(self.resource.id, 'set').execute(
            self.plan.resource_id
        )


class Describe(SimpleDescribe, Plan):

    resource = Endpoint
    service_name = 'ec2'
    api_version = '2015-10-01'
    describe_action = 'describe_vpc_endpoints'
    describe_envelope = 'VpcEndpoints'
    key = 'VpcEndpointId'

    def get_describe_filters(self):
        vpc = self.runner.get_plan(self.resource.vpc)
        if not vpc.resource_id:
            return None

        vpce_id, _ = self.runner.get_service(self.resource.id, 'get').execute()
        if not vpce_id:
            return None

        return {
            'Filters': [
                {'Name': 'vpc-endpoint-id', 'Values': [vpce_id]},
            ]
        }


class Apply(SimpleApply, Describe):

    create_action = 'create_vpc_endpoint'

    def name_object(self):
        yield NameAction(self)


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_vpc_endpoints'

    def get_destroy_serializer(self):
        return serializers.Dict(
            VpcEndpointIds=serializers.ListOfOne(serializers.Identifier()),
        )
