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

from ..account import AWS
from ..common import SimpleApply


class VPC(Resource):

    resource_name = "vpc"

    name = argument.String()
    cidr_block = argument.IPNetwork()
    account = argument.Resource(AWS)


class AddVPC(Action):

    @property
    def description(self):
        yield "Add virtual private cloud '{}'".format(self.resource.name)

    def run(self):
        operation = self.target.service.get_operation("CreateVpc")
        response, data = operation.call(
            self.target.endpoint,
            CidrBlock=str(self.resource.cidr_block),
        )

        if response.status_code != 200:
            raise errors.Error("Unable to create VPC")

        # FIXME: Create and invoke CreateTags to set the name here.

        self.target.object = data

        waiter = self.target.service.get_waiter("VpcAvailable", self.target.endpoint)
        waiter.wait(VpcIds=[data['VpcId']])


class Apply(SimpleApply, Target):

    resource = VPC
    add_action = AddVPC
    key = 'VpcId'

    def get_object(self):
        operation = self.service.get_operation("DescribeVpcs")
        response, data = operation.call(self.endpoint)
        for vpc in data['Vpcs']:
            if vpc['CidrBlock'] == str(self.resource.cidr_block):
                return vpc
