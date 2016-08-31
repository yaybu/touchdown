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

from ..common import (
    Resource,
    SimpleApply,
    SimpleDescribe,
    SimpleDestroy,
    TagsMixin,
)
from .internet_gateway import InternetGateway
from .vpc import VPC
from .vpn_gateway import VpnGateway


class Route(Resource):

    resource_name = 'route'

    destination_cidr = argument.IPNetwork(field='DestinationCidrBlock')
    internet_gateway = argument.Resource(InternetGateway, field='GatewayId')
    nat_gateway = argument.Resource('touchdown.aws.vpc.nat_gateway.NatGateway', field='NatGatewayId')
    ignore = argument.Boolean(default=False)

    # instance = argument.Resource(Instance, field='InstanceId')
    # network_interface = argument.Resource(NetworkInterface, field='NetworkInterfaceId')
    # vpc_peering_connection = argument.Resource(VpcPeeringConnection, field='VpcPeeringConnectionId')

    def matches(self, runner, route):
        if self.ignore and route['DestinationCidrBlock'] == self.destination_cidr:
            return True
        return super(Route, self).matches(runner, route)


class RouteTable(Resource):

    resource_name = 'route_table'

    name = argument.String(field='Name', group='tags')
    routes = argument.ResourceList(Route)
    propagating_vpn_gateways = argument.ResourceList(VpnGateway)
    tags = argument.Dict()
    vpc = argument.Resource(VPC, field='VpcId')


class Describe(SimpleDescribe, Plan):

    resource = RouteTable
    service_name = 'ec2'
    api_version = '2015-10-01'
    describe_action = 'describe_route_tables'
    describe_envelope = 'RouteTables'
    key = 'RouteTableId'

    def get_describe_filters(self):
        vpc = self.runner.get_plan(self.resource.vpc)
        if not vpc.resource_id:
            return None

        return {
            'Filters': [
                {'Name': 'tag:Name', 'Values': [self.resource.name]},
            ],
        }


class Apply(TagsMixin, SimpleApply, Describe):

    create_action = 'create_route_table'
    waiter = 'route_table_available'
    waiter_eventual_consistency_threshold = 5

    def update_vpgw_associations(self):
        remote = set(r['GatewayId'] for r in self.object.get('PropagatingVgws', []))
        local = set()
        for vgw in self.resource.propagating_vpn_gateways:
            id = self.runner.get_plan(vgw).resource_id
            if not id or id not in remote:
                yield self.generic_action(
                    'Enable route propagation from vpn gateway {}'.format(vgw.name),
                    self.client.enable_vgw_route_propagation,
                    RouteTableId=serializers.Identifier(),
                    GatewayId=serializers.Identifier(inner=serializers.Const(vgw)),
                )
            if id:
                local.add(id)

        for vgw in remote.difference(local):
            yield self.generic_action(
                'Disable route propagation from vpn gateway {}'.format(vgw),
                self.client.disable_vgw_route_propagation,
                RouteTableId=serializers.Identifier(),
                GatewayId=serializers.Const(vgw),
            )

    def update_routes(self):
        '''
        Compare the individual routes listed in the RouteTable to the ones
        defined in the current workspace, creating and removing routes as
        needed.

        Old routes are removed *before* new routes are added. This may cause
        connection glitches when applied, but it avoids route collisions.
        '''
        remote_routes = list(d for d in self.object.get('Routes', []) if d.get('GatewayId', '') != 'local')
        remote_routes = list(d for d in remote_routes if d['Origin'] != 'EnableVgwRoutePropagation')

        if remote_routes:
            for remote in remote_routes:
                for local in self.resource.routes:
                    if local.matches(self.runner, remote):
                        break
                else:
                    yield self.generic_action(
                        'Remove route for {}'.format(remote['DestinationCidrBlock']),
                        self.client.delete_route,
                        RouteTableId=serializers.Identifier(),
                        DestinationCidrBlock=remote['DestinationCidrBlock'],
                    )

        if self.resource.routes:
            for local in self.resource.routes:
                if local.ignore:
                    continue

                for remote in remote_routes:
                    if local.matches(self.runner, remote):
                        break
                else:
                    yield self.generic_action(
                        'Adding route for {}'.format(local.destination_cidr),
                        self.client.create_route,
                        local.serializer_with_kwargs(
                            RouteTableId=self.resource.identifier(),
                        ),
                    )

    def update_object(self):
        for action in super(Apply, self).update_object():
            yield action
        for action in self.update_routes():
            yield action
        for action in self.update_vpgw_associations():
            yield action


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_route_table'
