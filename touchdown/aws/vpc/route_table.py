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
from touchdown.core.renderable import ResourceId
from touchdown.core import argument

from .vpc import VPC
from .subnet import Subnet
from ..common import SimpleApply


class RouteTable(Resource):

    resource_name = "route_table"

    name = argument.String()
    vpc = argument.Resource(VPC, aws_field='VpcId')
    subnets = argument.ResourceList(Subnet)
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

    def update_object(self):
        for action in super(Apply, self).update_object():
            yield action

        remote_subnets = {}
        for association in self.object.get("Associations", []):
            remote_subnets[association['SubnetId']] = association['RouteTableAssociationId']

        for subnet in self.resource.subnets:
            subnet_id = self.runner.get_target(subnet).resource_id
            if not subnet_id or subnet_id not in remote_subnets:
                yield self.generic_action(
                    "Associate with subnet {}".format(subnet.name),
                    self.client.associate_route_table,
                    SubnetId=ResourceId(subnet),
                    RouteTableId=ResourceId(self),
                )

        # If we are the main table then we may be associated with non-managed
        # tables. Don't try and remove them...
        if not self.object.get("MainTable", False):
            return

        local_subnets = []
        for subnet in self.subnets:
            subnet_id = self.runner.get_target(subnet).resource_id
            if subnet_id:
                local_subnets.append(subnet_id)

        for subnet, association in remote_subnets.items():
            if subnet not in remote_subnets:
                yield self.generic_action(
                    "Disassociate from subnet {}".format(subnet),
                    self.client.disassociate_route_table,
                    AssociationId=association,
                )
