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
from touchdown.core import argument

from .vpc import VPC
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy


class CustomerGateway(Resource):

    """
    You can create an customer gateway in any VPC::

        customer_gateway = vpc.add_customer_gateway(
            name='my-customer-gateway',
        )
    """

    resource_name = "customer_gateway"

    name = argument.String()
    """ The name of the internet gateway. This field is required."""

    type = argument.String(default="ipsec.1", choices=["ipsec.1"], field="GatewayType")
    """ The type of VPN connection that this customer gateway supports """

    public_ip = argument.IPAddress(field="PublicIp")
    """ The internet-routable IP address for the customer gateway's outside interface. """

    bgp_asn = argument.Integer(default=65000, field="BgpAsn")
    """ For devices that support BGP, the gateway's BGP ASN """

    tags = argument.Dict()
    """ A dictionary of tags to associate with this VPC. A common use of tags
    is to group components by environment (e.g. "dev1", "staging", etc) or to
    map components to cost centres for billing purposes. """

    vpc = argument.Resource(VPC)


class Describe(SimpleDescribe, Target):

    resource = CustomerGateway
    service_name = 'ec2'
    describe_action = "describe_internet_gateways"
    describe_list_key = "CustomerGateways"
    key = "CustomerGatewayId"

    def get_describe_filters(self):
        return {
            "Filters": [
                {'Name': 'tag:Name', 'Values': [self.resource.name]},
            ],
        }


class Apply(SimpleApply, Describe):

    create_action = "create_customer_gateway"


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_customer_gateway"
