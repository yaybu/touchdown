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

from touchdown.core import serializers
from .vpc import VPC
from .internet_gateway import InternetGateway
from .vpn_gateway import VpnGateway
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy


class Route(Resource):

    """
    Represents a route in a route table.

    You shouldn't create Route resources directly, they are created
    implicitly when defining a :py:class:`RouteTable`. For example::

        vpc.add_route_table(
            name="internet_access",
            routes=[
                {"destionation_cidr": "8.8.8.8/32", "internet_gateway": ig},
                {"destionation_cidr": "8.8.4.4/32", "internet_gateway": ig},
            ]
        )
    """

    resource_name = "route"

    destination_cidr = argument.IPNetwork(field="DestinationCidrBlock")
    """ A network range that this rule applies to in CIDR form. You can specificy a single IP address with /32. For example, ``8.8.8.8/32``. To apply a default catch all rule you can specify ``0.0.0.0/32``. """

    internet_gateway = argument.Resource(InternetGateway, field="GatewayId")
    """ A :py:class:`InternetGateway` resource """

    # instance = argument.Resource(Instance, field="InstanceId")
    # network_interface = argument.Resource(NetworkInterface, field="NetworkInterfaceId")
    # vpc_peering_connection = argument.Resource(VpcPeeringConnection, field="VpcPeeringConnectionId")


class RouteTable(Resource):

    """
    A route table contains a list of routes. These are rules that are used to
    determine where to direct network traffic.

    A route table entry consists of a destination cidr and a component to use
    when to route that traffic. It is represented in touchdown by a
    :py:class:`Route` resource.

    You can create a route table in any vpc::

        vpc.add_route_table(
            name="internet_access",
            subnets=[subnet],
            routes=[dict(
                destination_cidr='0.0.0.0/0',
                internet_gateway=internet_gateway,
            )]
        )
    """

    resource_name = "route_table"

    name = argument.String()
    """ The name of the route table. This field is required."""

    routes = argument.ResourceList(Route)
    """ A list of :py:class:`Route` resources to ensure exist in the route
    table """

    propagating_vpn_gateways = argument.ResourceList(VpnGateway)
    """ A list of :py:class:`VpnGateway` resources that should propagate their
    routes into this route table """

    tags = argument.Dict()
    """ A dictionary of tags to associate with this VPC. A common use of tags
    is to group components by environment (e.g. "dev1", "staging", etc) or to
    map components to cost centres for billing purposes. """

    vpc = argument.Resource(VPC, field='VpcId')


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

    def update_vpgw_associations(self):
        remote = set(r['GatewayId'] for r in self.object.get("PropagatingsVgws", []))
        local = set()
        for vgw in self.resource.propagating_vpn_gateways:
            id = self.runner.get_target(vgw).resource_id
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
        for action in self.update_vpgw_associations():
            yield action


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_route_table"
