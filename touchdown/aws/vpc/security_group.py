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


class SecurityGroup(Resource):

    resource_name = "security_group"

    name = argument.String()
    description = argument.String()
    vpc = argument.Resource(VPC)
    tags = argument.Dict()


class AddSecurityGroup(Action):

    @property
    def description(self):
        yield "Add security group {}".format(self.resource.name)

    def run(self):
        vpc = self.get_target(self.resource.vpc)

        params = {
            'GroupName': self.resource.name,
            'VpcId': vpc.object['VpcId'],
        }

        if self.resource.description:
            params['Description'] = self.resource.description

        self.target.object = vpc.client.create_security_group(**params)


class Apply(SimpleApply, Target):

    resource = SecurityGroup
    add_action = AddSecurityGroup
    key = 'SecurityGroupId'

    def get_object(self, runner):
        vpc = runner.get_target(self.resource.vpc)
        self.client = vpc.client

        groups = self.client.describe_security_groups(
            Filters=[
                {'Name': 'group-name', 'Values': [self.resource.name]},
                {'Name': 'vpc-id', 'Values': [vpc.resource_id]}
            ],
        )

        if len(groups['SecurityGroups']) > 1:
            raise errors.Error("Too many possible security groups found")

        if groups['SecurityGroups']:
            return groups['SecurityGroups'][0]
