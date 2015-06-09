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

import base64

from touchdown.core.plan import Plan, Present
from touchdown.core import argument

from ..account import BaseAccount
from ..vpc import SecurityGroup
from ..iam import InstanceProfile
from ..common import Resource, SimpleDescribe, SimpleApply, SimpleDestroy
from touchdown.core import serializers
from touchdown.core.utils import force_str

from .keypair import KeyPair


class LaunchConfiguration(Resource):

    resource_name = "launch_configuration"

    name = argument.String(max=255, field="LaunchConfigurationName", update=False)

    image = argument.String(max=255, field="ImageId")

    key_pair = argument.Resource(KeyPair, field="KeyName")

    security_groups = argument.ResourceList(SecurityGroup, field="SecurityGroups")

    user_data = argument.String(field="UserData")

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

    keep_last = argument.Integer(default=5)

    account = argument.Resource(BaseAccount)

    def matches(self, runner, remote):
        if "UserData" in remote and remote["UserData"]:
            remote["UserData"] = force_str(base64.b64decode(remote["UserData"]))
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

        try:
            serial = lc["LaunchConfigurationName"].rsplit(".", 1)[1]
            self.biggest_serial = max(int(serial), self.biggest_serial)
        except (IndexError, TypeError, ValueError):
            pass

        if self.resource.matches(self.runner, lc):
            return True


class Apply(SimpleApply, Describe):

    create_action = "create_launch_configuration"
    create_response = "not-that-useful"

    signature = (
        Present("image"),
        Present("instance_type"),
    )

    def get_create_serializer(self):
        return serializers.Resource(
            LaunchConfigurationName=".".join((
                self.resource.name,
                str(self.biggest_serial + 1),
            )),
        )

    def prepare_to_create(self):
        prefix = "{}.".format(self.resource.name)
        configs = []
        for page in self.client.get_paginator("describe_launch_configurations").paginate():
            for config in page.get('LaunchConfigurations', []):
                if not config['LaunchConfigurationName'].startswith(prefix):
                    continue
                if self.object and config['LaunchConfigurationName'] == self.object['LaunchConfigurationName']:
                    # Make sure we don't delete the launch config that matches self.resource!!!
                    continue
                configs.append({
                    "LaunchConfigurationName": config["LaunchConfigurationName"],
                    "CreatedTime": config["CreatedTime"],
                })

        configs.sort(key=lambda config: config["CreatedTime"])

        for config in configs[:-self.resource.keep_last]:
            yield self.generic_action(
                "Delete stale configuration: {}".format(config['LaunchConfigurationName']),
                self.client.delete_launch_configuration,
                LaunchConfigurationName=config['LaunchConfigurationName'],
            )


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_launch_configuration"
