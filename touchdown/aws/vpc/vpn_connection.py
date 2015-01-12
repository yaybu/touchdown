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

from touchdown.core.resource import Resource
from touchdown.core.target import Target
from touchdown.core import argument, serializers

from .vpc import VPC
from .customer_gateway import CustomerGateway
from .vpn_gateway import VpnGateway
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy


class VpnConnection(Resource):

    """
    You can create a VPN Connection in any VPC::

        vpn = vpn.add_vpn_connection(
            name='my-vpn-connection',
        )
    """

    resource_name = "vpn_connection"

    name = argument.String()
    """ The name of the vpn connection. This field is required."""

    customer_gateway = argument.Resource(CustomerGateway, field="CustomerGatewayId")
    """ A :py:class:`CustomerGateway`. This field is required. """

    vpn_gateway = argument.Resource(VpnGateway, field="VpnGatewayId")
    """ A :py:class:`VpnGateway`. This field is required. """

    type = argument.String(default="ipsec.1", choices=["ipsec.1"], field="Type")
    """ The type of VPN connection to create """

    static_routes_only = argument.Boolean(
        default=True,
        field="Options",
        serializer=serializers.Dict(StaticRoutesOnly=serializers.Boolean()),
    )

    static_routes = argument.List()
    # FIXME: This should somehow be a list of argument.IPNetwork

    tags = argument.Dict()
    """ A dictionary of tags to associate with this VPC. A common use of tags
    is to group components by environment (e.g. "dev1", "staging", etc) or to
    map components to cost centres for billing purposes. """

    vpc = argument.Resource(VPC)


class Describe(SimpleDescribe, Target):

    resource = CustomerGateway
    service_name = 'ec2'
    describe_action = "describe_vpn_connections"
    describe_list_key = "VpnConnections"
    key = "VpnConnectionId"

    def get_describe_filters(self):
        return {
            "Filters": [
                {'Name': 'tag:Name', 'Values': [self.resource.name]},
            ],
        }


class Apply(SimpleApply, Describe):

    create_action = "create_vpn_connection"

    def update_object(self):
        remote_routes = set(r['DestinationCidrBlock'] for r in self.object.get('Routes', []) if r['State'] != 'deleted')
        local_routes = set(self.resource.static_routes)

        for route in local_routes.difference(remote_routes):
            yield self.generic_action(
                "Add missing route {}".format(route),
                self.client.create_vpn_connection_route,
                VpnConnectionId=serializers.Identifier(),
                DestinationCidrBlock=route,
            )

        for route in remote_routes.difference(local_routes):
            yield self.generic_action(
                "Remove stale route {}".format(route),
                self.client.create_vpn_connection_route,
                VpnConnectionId=serializers.Identifier(),
                DestinationCidrBlock=route,
            )


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_vpn_connection"
