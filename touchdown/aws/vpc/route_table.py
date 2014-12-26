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

from botocore import session

from touchdown.core.resource import Resource
from touchdown.core.policy import Policy
from touchdown.core.action import Action
from touchdown.core import argument, errors

from .vpc import VPC
from ..common import SimpleApply


class RouteTable(Resource):

    resource_name = "route-table"

    name = argument.String()
    vpc = argument.Resource(VPC)


class AddRouteTable(Action):

    @property
    def description(self):
        yield "Add route table"

    def run(self):
        operation = self.policy.service.get_operation("CreateRouteTable")
        response, data = operation.call(
            self.policy.endpoint,
            VpcId=self.resource.parent.resource_id,
        )

        if response.status_code != 200:
            raise errors.Error("Unable to create route table")

        # FIXME: Create and invoke CreateTags to set the name here.


class Apply(SimpleApply, Policy):

    resource = RouteTable
    add_action = AddRouteTable
    key = "RouteTableId"

    def get_object(self):
        operation = self.service.get_operation("DescribeRouteTables")
        response, data = operation.call(
            self.endpoint,
            Filters=[
                #{'Name': 'attachement.vpc-id', 'Values': [self.resource.cidr_block]},
            ],
        )
        if len(data['RouteTables']) > 0:
            raise errors.Error("Too many possible gateways found")
        if data['RouteTables']:
            return data['RouteTables'][0]
