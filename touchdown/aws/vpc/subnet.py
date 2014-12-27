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

        self.target.object = vpc.client.create_subnet(
            VpcId=vpc.object['VpcId'],
            CidrBlock=str(self.resource.cidr_block),
        )


class Apply(SimpleApply, Target):

    resource = Subnet
    add_action = AddSubnet
    key = 'SubnetId'

    def get_object(self, runner):
        self.client = runner.get_target(self.resource.vpc).client

        subnets = self.client.describe_subnets(
            Filters=[
                {'Name': 'cidrBlock', 'Values': [str(self.resource.cidr_block)]},
            ],
        )

        if len(subnets['Subnets']) > 1:
            raise errors.Error("Too many possible subnets found")

        if subnets['Subnets']:
            return subnets['Subnets'][0]
