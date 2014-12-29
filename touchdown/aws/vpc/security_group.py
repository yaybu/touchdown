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

    name = argument.String(aws_field="GroupName")
    description = argument.String(aws_field="Description")
    vpc = argument.Resource(VPC, aws_field="VpcId")
    tags = argument.Dict()


class Apply(SimpleApply, Target):

    resource = SecurityGroup
    create_action = "create_security_group"
    describe_action = "describe_security_groups"
    describe_list_key = "SecurityGroups"
    key = 'SecurityGroupId'

    def get_describe_filter(self):
        vpc = runner.get_target(self.resource.vpc)
        self.client = vpc.client

        return {
            "Filters":[
                {'Name': 'group-name', 'Values': [self.resource.name]},
                {'Name': 'vpc-id', 'Values': [vpc.resource_id]}
            ],
        }
