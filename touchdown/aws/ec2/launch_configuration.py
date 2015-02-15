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

from touchdown.core.plan import Plan
from touchdown.core import argument

from ..account import Account
from ..vpc import SecurityGroup
from ..iam import InstanceProfile
from ..common import Resource, SimpleDescribe, SimpleApply, SimpleDestroy
from touchdown.core import serializers

from .keypair import KeyPair


class LaunchConfiguration(Resource):

    resource_name = "launch_configuration"

    name = argument.String(max=255, field="LaunchConfigurationName", update=False)

    image = argument.String(max=255, field="ImageId")

    key_pair = argument.Resource(KeyPair, field="KeyName")

    security_groups = argument.ResourceList(SecurityGroup, field="SecurityGroups")

    user_data = argument.Serializer(field="UserData")

    instance_type = argument.String(max=255, field="InstanceType")

    kernel = argument.String(max=255, field="KernelId")

    ramdisk = argument.String(max=255, field="RamdiskId")

    # block_devices = argument.Dict(field="BlockDeviceMappings")

    instance_monitoring = argument.Boolean(
        default=False,
        field="InstanceMonitoring",
        serializer=serializers.Dict(Enabled=serializers.Identity()),
    )

    spot_price = argument.String(field="SpotPrice")

    instance_profile = argument.Resource(
        InstanceProfile,
        field="IamInstanceProfile",
        serializers=serializers.Property("Arn"),
    )

    ebs_optimized = argument.Boolean(field="EbsOptimized")

    associate_public_ip_address = argument.Boolean(field="AssociatePublicIpAddress")

    placement_tenancy = argument.String(
        max=64,
        choices=[
            "default",
            "dedicated",
        ],
        field="PlacementTenancy",
    )

    account = argument.Resource(Account)

    def matches(self, runner, remote):
        if "UserData" in remote and remote["UserData"]:
            import base64
            remote["UserData"] = base64.b64decode(remote["UserData"])
        return super(LaunchConfiguration, self).matches(runner, remote)


class Describe(SimpleDescribe, Plan):

    resource = LaunchConfiguration
    service_name = 'autoscaling'
    describe_action = "describe_launch_configurations"
    describe_envelope = "LaunchConfigurations"
    describe_filters = {}
    key = 'LaunchConfigurationName'

    biggest_serial = 0

    def describe_object_matches(self, lc):
        if not lc["LaunchConfigurationName"].startswith(self.resource.name + "."):
            return False

        serial = lc["LaunchConfigurationName"].rsplit(".", 1)[1]
        self.biggest_serial = max(int(serial), self.biggest_serial)

        if self.resource.matches(self.runner, lc):
            return True


class Apply(SimpleApply, Describe):

    create_action = "create_launch_configuration"
    create_response = "not-that-useful"

    def get_create_serializer(self):
        return serializers.Resource(
            LaunchConfigurationName=".".join((
                self.resource.name,
                str(self.biggest_serial + 1),
            )),
        )


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_launch_configuration"
