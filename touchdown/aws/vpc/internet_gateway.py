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

from .vpc import VPC
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy


class InternetGateway(Resource):

    """
    An internet gateway is the AWS component that allows you to physically
    connect your VPC to the internet. Without an internet gateawy connected to
    your VPC then traffic will not reach it, even if assigned public IP
    addresses.

    You can create an internet gateway in any VPC::

        internet_gateway = vpc.add_internet_gateway(
            name='my-internet-gateway',
        )
    """

    resource_name = "internet_gateway"

    name = argument.String()
    """ The name of the internet gateway. This field is required."""

    tags = argument.Dict()
    """ A dictionary of tags to associate with this VPC. A common use of tags
    is to group components by environment (e.g. "dev1", "staging", etc) or to
    map components to cost centres for billing purposes. """

    vpc = argument.Resource(VPC)


class Describe(SimpleDescribe, Plan):

    resource = InternetGateway
    service_name = 'ec2'
    describe_action = "describe_internet_gateways"
    describe_list_key = "InternetGateways"
    key = "InternetGatewayId"

    def get_describe_filters(self):
        return {
            "Filters": [
                {'Name': 'tag:Name', 'Values': [self.resource.name]},
            ],
        }


class Apply(SimpleApply, Describe):

    create_action = "create_internet_gateway"


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_internet_gateway"
