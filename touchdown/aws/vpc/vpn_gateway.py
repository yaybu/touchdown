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
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy


class VpnGateway(Resource):

    """
    You can create an vpn gateway in any VPC::

        customer_gateway = vpc.add_vpn_gateway(
            name='my-vpn-gateway',
        )
    """

    resource_name = "vpn_gateway"

    name = argument.String()
    """ The name of the internet gateway. This field is required."""

    type = argument.String(default="ipsec.1", choices=["ipsec.1"], field="Type")
    """ The type of VPN connection that this VPN gateway supports """

    availability_zone = argument.String(field="AvailabilityZone")
    """ The availability zone to place the Vpn Gateway in """

    tags = argument.Dict()
    """ A dictionary of tags to associate with this VPC. A common use of tags
    is to group components by environment (e.g. "dev1", "staging", etc) or to
    map components to cost centres for billing purposes. """

    vpc = argument.Resource(VPC)


class Describe(SimpleDescribe, Target):

    resource = VpnGateway
    service_name = 'ec2'
    describe_action = "describe_vpn_gateways"
    describe_list_key = "VpnGateways"
    key = "VpnGatewayId"

    def get_describe_filters(self):
        return {
            "Filters": [
                {'Name': 'tag:Name', 'Values': [self.resource.name]},
            ],
        }


class Apply(SimpleApply, Describe):

    create_action = "create_vpn_gateway"

    def update_object(self):
        if not self.object:
            yield self.generic_action(
                "Attach gateway to vpc",
                self.client.attach_vpn_gateway,
                VpnGatewayId=serializers.Identifier(),
                VpcId=serializers.Context(serializers.Argument("vpc"), serializers.Identifer()),
            )


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_vpn_gateway"
