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

from ..account import Account
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy


class VPC(Resource):

    """
    Represents a Virtual Private Cloud in an amazon region.

    VPC's let you logically isolate components of your system. A properly
    defined VPC allows you to run most of your backend components on private IP
    addresses - shielding it from the public internet.

    You can add a VPC to your workspace from any Amazon account resource::

        account = workspace.add_aws(
            access_key_id='....',
            secret_access_key='....',
            region='eu-west-1',
        )

        vpc = workspace.add_vpc(
            name='my-first-vpc',
            cidr_block='10.0.0.0/16',
        )
    """

    resource_name = "vpc"

    name = argument.String()
    """ The name of the VPC. This field is required."""

    cidr_block = argument.IPNetwork(field='CidrBlock')
    """ A network range in CIDR form. For example, 10.0.0.0/16. A VPC network
    should only use private IPs, and not public addresses. This field is
    required."""

    tenancy = argument.String(default="default", choices=["default", "dedicated"], field="InstanceTenancy")
    """ This controls whether or not to enforce use of single-tenant hardware
    for this VPC. If set to ``default`` then instances can be launched with any
    tenancy options. If set to ``dedicated`` then all instances started in this
    VPC will be launched as dedicated tenancy, regardless of the tenancy they
    requsest. """

    tags = argument.Dict()
    """ A dictionary of tags to associate with this VPC. A common use of tags
    is to group components by environment (e.g. "dev1", "staging", etc) or to
    map components to cost centres for billing purposes. """

    account = argument.Resource(Account)


class Describe(SimpleDescribe, Target):

    resource = VPC
    service_name = 'ec2'
    describe_action = "describe_vpcs"
    describe_list_key = "Vpcs"
    key = 'VpcId'

    def get_describe_filters(self):
        return {
            "Filters": [
                {'Name': 'tag:Name', 'Values': [self.resource.name]},
            ],
        }


class Apply(SimpleApply, Describe):

    create_action = "create_vpc"
    waiter = 'vpc_available'


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_vpc"
    waiter = 'vpc_terminated'
