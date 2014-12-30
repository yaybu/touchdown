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
from touchdown.core.target import Target
from touchdown.core import argument

from .vpc import VPC
from ..common import SimpleApply


class RouteTable(Resource):

    resource_name = "route_table"

    name = argument.String()
    vpc = argument.Resource(VPC, aws_field='VpcId')
    tags = argument.Dict()


class Apply(SimpleApply, Target):

    resource = RouteTable
    create_action = "create_route_table"
    describe_action = "describe_route_tables"
    describe_list_key = "RouteTables"
    key = "RouteTableId"

    @property
    def client(self):
        return self.runner.get_target(self.resource.vpc).client

    def get_describe_filters(self):
        return {
            "Filters": [
                {'Name': 'tag:name', 'Values': [self.resource.name]},
            ],
        }
