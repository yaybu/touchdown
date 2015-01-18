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
from touchdown.core.plan import Plan
from touchdown.core import argument

from touchdown.core import serializers
from .vpc import VPC
from .internet_gateway import InternetGateway
from .vpn_gateway import VpnGateway
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy


class Route(Resource):

    resource_name = "route"

    destination_cidr = argument.IPNetwork(field="DestinationCidrBlock")
    internet_gateway = argument.Resource(InternetGateway, field="GatewayId")

    # instance = argument.Resource(Instance, field="InstanceId")
    # network_interface = argument.Resource(NetworkInterface, field="NetworkInterfaceId")
    # vpc_peering_connection = argument.Resource(VpcPeeringConnection, field="VpcPeeringConnectionId")

    def matches(self, runner, remote):
        for name, arg in self.arguments:
            if not arg.present(self):
                continue
            if not arg.field:
                continue
            if arg.field not in remote:
                return False
            if arg.serializer.render(runner, getattr(self, name)) != remote[arg.field]:
                return False

        return True


class RouteTable(Resource):

    resource_name = "route_table"

    name = argument.String()
    routes = argument.ResourceList(Route)
    propagating_vpn_gateways = argument.ResourceList(VpnGateway)
    tags = argument.Dict()
    vpc = argument.Resource(VPC, field='VpcId')


class Describe(SimpleDescribe, Plan):

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

    def update_vpgw_associations(self):
        remote = set(r['GatewayId'] for r in self.object.get("PropagatingsVgws", []))
        local = set()
        for vgw in self.resource.propagating_vpn_gateways:
            id = self.runner.get_plan(vgw).resource_id
            if not id or id not in remote:
                yield self.generic_action(
                    "Enable route propagation from vpn gateway {}".format(vgw.name),
                    self.client.enable_vgw_route_propagation,
                    RouteTableId=serializers.Identifier(),
                    GatewayId=serializers.Identifier(inner=serializers.Const(vgw)),
                )
            if id:
                local.add(id)

        for vgw in remote.difference(local):
            yield self.generic_action(
                "Disable route propagation from vpn gateway {}".format(vgw),
                self.client.disable_vgw_route_propagation,
                RouteTableId=serializers.Identifier(),
                GatewayId=serializers.Const(inner=serializers.Const(vgw)),
            )

    def update_associations(self):
        return

        remote_subnets = {}
        for association in self.object.get("Associations", []):
            remote_subnets[association['SubnetId']] = association['RouteTableAssociationId']

        for subnet in self.resource.subnets:
            subnet_id = self.runner.get_plan(subnet).resource_id
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
            subnet_id = self.runner.get_plan(subnet).resource_id
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
        remote_routes = (d for d in self.object.get("Routes", []) if d["GatewayId"] != "local")

        if remote_routes:
            for remote in remote_routes:
                for local in self.resource.routes:
                    if local.matches(self.runner, remote):
                        continue
                    break
                else:
                    yield self.generic_action(
                        "Remove route for {}".format(remote['DestinationCidrBlock']),
                        self.client.delete_route,
                        RouteTableId=serializers.Identifier(),
                        DestinationCidrBlock=remote['DestinationCidrBlock'],
                    )

        if self.resource.routes:
            for local in self.resource.routes:
                for remote in remote_routes:
                    if local.matches(self.runner, remote):
                        continue
                    break
                else:
                    yield self.generic_action(
                        "Adding route for {}".format(local.destination_cidr),
                        self.client.create_route,
                        serializers.Context(serializers.Const(local), serializers.Resource(
                            RouteTableId=serializers.Identifier(serializers.Const(self.resource)),
                        ))
                    )

    def update_object(self):
        for action in super(Apply, self).update_object():
            yield action
        for action in self.update_associations():
            yield action
        for action in self.update_routes():
            yield action
        for action in self.update_vpgw_associations():
            yield action


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_route_table"
