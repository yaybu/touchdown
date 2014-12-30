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

from .vpc import VPC
from ..common import SimpleApply


class Subnet(Resource):

    resource_name = "subnet"

    name = argument.String()
    cidr_block = argument.IPNetwork(aws_field='CidrBlock')
    availability_zone = argument.String(aws_field='AvailabilityZone')
    vpc = argument.Resource(VPC, aws_field='VpcId')
    tags = argument.Dict()


class Apply(SimpleApply, Target):

    resource = Subnet
    create_action = "create_subnet"
    describe_action = "describe_subnets"
    describe_list_key = "Subnets"
    key = 'SubnetId'

    @property
    def client(self):
        return self.runner.get_target(self.resource.vpc).client

    def get_describe_filters(self):
        return {
            "Filters": [
                {'Name': 'cidrBlock', 'Values': [str(self.resource.cidr_block)]},
            ],
        }
