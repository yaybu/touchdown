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

from ..account import AWS
from ..vpc import SecurityGroup
from ..iam import InstanceProfile
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy
from .. import serializers

from .keypair import KeyPair


class LaunchConfiguration(Resource):

    resource_name = "launch_configuration"

    """ A name for this AutoScalingGroup. Unique within an AWS account """
    name = argument.String(max=255, aws_field="LaunchConfigurationName")

    image = argument.String(max=255, aws_field="ImageId")

    key_pair = argument.Resource(KeyPair, aws_field="KeyName")

    security_groups = argument.ResourceList(SecurityGroup, aws_field="SecurityGroups")

    user_data = argument.Serializer(aws_field="UserData")

    instance_type = argument.String(max=255, aws_field="InstanceType")

    kernel = argument.String(max=255, aws_field="KernelId")

    ramdisk = argument.String(max=255, aws_field="RamdiskId")

    # block_devices = argument.Dict(aws_field="BlockDeviceMappings")

    instance_monitoring = argument.Boolean(default=False, aws_field="InstanceMonitoring", aws_serializer=serializers.Dict(Enabled=serializers.Identity()))

    spot_price = argument.String(aws_field="SpotPrice")

    instance_profile = argument.Resource(InstanceProfile, aws_field="IamInstanceProfile")

    ebs_optimized = argument.Boolean(aws_field="EbsOptimized")

    associate_public_ip_address = argument.Boolean(aws_field="AssociatePublicIpAddress")

    placement_tenancy = argument.String(
        max=64,
        choices=[
            "default",
            "dedicated",
        ],
        aws_field="PlacementTenancy",
    )

    account = argument.Resource(AWS)

    def matches(self, runner, object):
        if object['ImageId'] != self.image:
            return False
        if self.key_pair and self.key_pair.name != object['KeyName']:
            return False
        #if object['UserData'] != self.user_data:
        #    return False
        #if object['IamInstanceProfile'] != runner.get_target(self.instance_profile).resource_id:
        #    return False
        # FIXME: Match more things
        return True


class Describe(SimpleDescribe, Target):

    resource = LaunchConfiguration
    service_name = 'autoscaling'
    describe_action = "describe_launch_configurations"
    describe_list_key = "LaunchConfigurations"
    key = 'LaunchConfigurationName'

    def describe_object(self):
        for launch_config in self.client.describe_launch_configurations()['LaunchConfigurations']:
            if self.resource.matches(self.runner, launch_config):
                return launch_config


class Apply(SimpleApply, Describe):

    create_action = "create_launch_configuration"


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_launch_configuration"
