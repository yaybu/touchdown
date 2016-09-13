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

from touchdown.core import argument, resource, serializers
from touchdown.core.plan import Plan, Present
from touchdown.core.utils import force_str

from ..account import BaseAccount
from ..iam import InstanceProfile
from ..replacement import (
    ReplacementApply,
    ReplacementDescribe,
    ReplacementDestroy,
)
from ..vpc import SecurityGroup
from .keypair import KeyPair


class LaunchConfiguration(resource.Resource):

    resource_name = 'launch_configuration'

    name = argument.String(max=255, field='LaunchConfigurationName', update=False)

    image = argument.String(max=255, field='ImageId')

    key_pair = argument.Resource(KeyPair, field='KeyName')

    security_groups = argument.ResourceList(SecurityGroup, field='SecurityGroups')

    user_data = argument.String(field='UserData')

    json_user_data = argument.Dict(
        field='UserData',
        default=None,
        serializer=serializers.Json(serializers.Map()),
    )

    instance_type = argument.String(max=255, field='InstanceType')

    kernel = argument.String(max=255, field='KernelId')

    ramdisk = argument.String(max=255, field='RamdiskId')

    # block_devices = argument.Dict(field='BlockDeviceMappings')

    instance_monitoring = argument.Boolean(
        default=False,
        field='InstanceMonitoring',
        serializer=serializers.Dict(Enabled=serializers.Identity()),
    )

    spot_price = argument.String(field='SpotPrice')

    instance_profile = argument.Resource(
        InstanceProfile,
        field='IamInstanceProfile',
        serializers=serializers.Property('Arn'),
    )

    ebs_optimized = argument.Boolean(field='EbsOptimized')

    associate_public_ip_address = argument.Boolean(field='AssociatePublicIpAddress')

    placement_tenancy = argument.String(
        max=64,
        choices=[
            'default',
            'dedicated',
        ],
        field='PlacementTenancy',
    )

    account = argument.Resource(BaseAccount)


class Describe(ReplacementDescribe, Plan):

    resource = LaunchConfiguration
    service_name = 'autoscaling'
    api_version = '2011-01-01'
    describe_action = 'describe_launch_configurations'
    describe_envelope = 'LaunchConfigurations'
    describe_filters = {}
    key = 'LaunchConfigurationName'

    _active_launch_configs = None

    @property
    def active_launch_configs(self):
        if not self._active_launch_configs:
            active = self._active_launch_configs = set()
            dasg = self.client.get_paginator('describe_auto_scaling_groups')
            for page in dasg.paginate():
                for asg in page.get('AutoScalingGroups', []):
                    active.add(asg['LaunchConfigurationName'])
        return self._active_launch_configs

    def get_possible_objects(self):
        for obj in super(Describe, self).get_possible_objects():
            if 'UserData' in obj and obj['UserData']:
                obj['UserData'] = force_str(base64.b64decode(obj['UserData']))
            yield obj


class Apply(ReplacementApply, Describe):

    create_action = 'create_launch_configuration'
    create_response = 'not-that-useful'
    destroy_action = 'delete_launch_configuration'

    signature = (
        Present('image'),
        Present('instance_type'),
    )

    def is_stale(self, launch_config):
        # Don't try and delete launch configuration that are still in use
        if launch_config['LaunchConfigurationName'] in self.active_launch_configs:
            return False
        return super(Apply, self).is_stale(launch_config)


class Destroy(ReplacementDestroy, Describe):

    destroy_action = 'delete_launch_configuration'
