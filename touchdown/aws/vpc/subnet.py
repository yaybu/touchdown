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

from botocore import session

from touchdown.core.resource import Resource
from touchdown.core.policy import Policy
from touchdown.core.action import Action
from touchdown.core import argument, errors

from .vpc import VPC
from ..common import SimpleApply


class Subnet(Resource):

    resource_name = "subnet"

    name = argument.String()
    cidr_block = argument.IPNetwork()
    vpc = argument.Resource(VPC)


class AddSubnet(Action):

    @property
    def description(self):
        yield "Add subnet for {} to virtual private cloud".format(
            self.resource.cidr_block,
        )

    def run(self):
        vpc = self.get_target(self.resource.vpc)

        operation = self.policy.service.get_operation("CreateSubnet")
        response, data = operation.call(
            self.policy.endpoint,
            VpcId=vpc.object['VpcId'],
            CidrBlock=str(self.resource.cidr_block),
        )

        if response.status_code != 200:
            raise errors.Error("Unable to create subnet")

        # FIXME: Create and invoke CreateTags to set the name here.


class Apply(SimpleApply, Policy):

    resource = Subnet
    add_action = AddSubnet
    key = 'SubnetId'

    def get_object(self):
        operation = self.service.get_operation("DescribeSubnets")
        response, data = operation.call(
            self.endpoint,
            Filters=[
                {'Name': 'cidrBlock', 'Values': [str(self.resource.cidr_block)]},
            ],
        )

        if len(data['Subnets']) > 0:
            raise errors.Error("Too many possible subnets found")
        if data['Subnets']:
            return data['Subnets'][0]
