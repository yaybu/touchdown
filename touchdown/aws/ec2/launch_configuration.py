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
from ..common import SimpleApply


class LaunchConfiguration(Resource):

    resource_name = "launch_configuration"

    """ A name for this AutoScalingGroup. Unique within an AWS account """
    name = argument.String(max=255, aws_field="LaunchConfigurationName")

    image = argument.String(max=255, aws_field="ImageId")

    key_name = argument.String(max=255, aws_field="KeyName")

    security_groups = argument.ResourceList(SecurityGroup, aws_field="SecurityGroups")

    user_data = argument.String()

    instance_type = argument.String(max=255, aws_field="InstanceType")

    kernel = argument.String(max=255, aws_field="KernelId")

    ramdisk = argument.String(max=255, aws_field="RamdiskId")

    # block_devices = argument.Dict(aws_field="BlockDeviceMappings")

    instance_monitoring = argument.Boolean(default=False, aws_field="InstanceMonitoring")

    spot_price = argument.String(aws_field="SpotPrice")

    instance_profile = argument.String(max=1600, aws_field="IamInstanceProfile")

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


class Apply(SimpleApply, Target):

    resource = LaunchConfiguration
    create_action = "create_auto_scaling_group"
    describe_action = "describe_launch_configurations"
    describe_list_key = "LaunchConfigurations"
    key = 'LaunchConfigurationId'

    @property
    def client(self):
        account = self.runner.get_target(self.resource.acount)
        return account.get_client('autoscale')
