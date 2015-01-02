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

class Rule(Resource):

    resource_name = "rule"

    protocol = argument.String(
        choices=['tcp', 'udp', 'icmp'],
        aws_field="IpProtocol",
    )

    from_port = argument.Integer(min=-1, max=32768, aws_field="FromPort")

    to_port = argument.Integer(min=-1, max=32768, aws_field="ToPort")

    # security_groups = argument.ResourceList(SecurityGroup)
    # FIXME: Need to fix the self-referencing problem with the models
    # FIXME: How to serialize a resource to a compound type...

    networks = argument.List(aws_field="IpRanges")
    # FIXME: How to serialize a lsit of IP addresses to {"CidrIp": IP}


class SecurityGroup(Resource):

    resource_name = "security_group"

    name = argument.String(aws_field="GroupName")
    description = argument.String(aws_field="Description")
    vpc = argument.Resource(VPC, aws_field="VpcId")
    ingress = argument.ResourceList(Rule)
    egress = argument.ResourceList(Rule)
    tags = argument.Dict()


class Apply(SimpleApply, Target):

    resource = SecurityGroup
    create_action = "create_security_group"
    describe_action = "describe_security_groups"
    describe_list_key = "SecurityGroups"
    key = 'SecurityGroupId'

    @property
    def client(self):
        return self.runner.get_target(self.resource.vpc).client

    def get_describe_filters(self):
        vpc = self.runner.get_target(self.resource.vpc)
        return {
            "Filters": [
                {'Name': 'group-name', 'Values': [self.resource.name]},
                {'Name': 'vpc-id', 'Values': [vpc.resource_id]}
            ],
        }

    def update_object(self):
        remote_rules = [hd(d) for d in self.object.get("IpPermissions", [])]

        remote_rules = self.objects.get("IpPermissionsEgress", [])
