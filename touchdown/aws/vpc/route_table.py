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

from .. import serializers
from .vpc import VPC
from .subnet import Subnet
from .internet_gateway import InternetGateway
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy


class Route(Resource):

    resource_name = "route"

    destination_cidr = argument.IPNetwork(aws_field="DestinationCidrBlock")
    internet_gateway = argument.Resource(InternetGateway, aws_field="GatewayId")
    # instance = argument.Resource(Instance, aws_field="InstanceId")
    # network_interface = argument.Resource(NetworkInterface, aws_field="NetworkInterfaceId")
    # vpc_peering_connection = argument.Resource(VpcPeeringConnection, aws_field="VpcPeeringConnectionId")


class RouteTable(Resource):

    resource_name = "route_table"

    name = argument.String()
    vpc = argument.Resource(VPC, aws_field='VpcId')
    subnets = argument.ResourceList(Subnet)
    routes = argument.List()
    tags = argument.Dict()


class Describe(SimpleDescribe, Target):

    resource = RouteTable
    service_name = 'ec2'
    describe_action = "describe_route_tables"
    describe_list_key = "RouteTables"
    key = "RouteTableId"

    def get_describe_filters(self):
        return {
            "Filters": [
                {'Name': 'tag:Name', 'Values': [self.resource.name]},
            ],
        }


class Apply(SimpleApply, Describe):

    create_action = "create_route_table"

    def update_associations(self):
        remote_subnets = {}
        for association in self.object.get("Associations", []):
            remote_subnets[association['SubnetId']] = association['RouteTableAssociationId']

        for subnet in self.resource.subnets:
            subnet_id = self.runner.get_target(subnet).resource_id
            if not subnet_id or subnet_id not in remote_subnets:
                yield self.generic_action(
                    "Associate with subnet {}".format(subnet.name),
                    self.client.associate_route_table,
                    SubnetId=serializers.Identifier(inner=serializers.Const(subnet)),
                    RouteTableId=serializers.Identifier(self),
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

    def update_routes(self):
        """
        Compare the individual routes listed in the RouteTable to the ones
        defined in the current workspace, creating and removing routes as
        needed.

        Old routes are removed *before* new routes are added. This may cause
        connection glitches when applied, but it avoids route collisions.
        """
        remote_routes = frozenset(serializers.hd(d) for d in self.object.get("routes", []))
        local_routes = frozenset(serializers.Resource(d).render(self.runner, d) for d in self.resource.routes)

        for route in (remote_routes - local_routes):
            yield self.generic_action(
                "Remove route for {}".format(route['DestinationCidrBlock']),
                RouteTableId=serializers.Identifier(self),
                **route
            )

        for route in (local_routes - remote_routes):
            yield self.generic_action(
                "Adding route for {}".format(route['DestinationCidrBlock']),
                self.client.create_route,
                RouteTableId=serializers.Identifier(self),
                **route
            )

    def update_object(self):
        for action in super(Apply, self).update_object():
            yield action
        for action in self.update_associations():
            yield action
        for action in self.update_routes():
            yield action


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_route_table"
