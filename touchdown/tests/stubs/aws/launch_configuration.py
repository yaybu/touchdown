# Copyright 2016 Isotoma Limited
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

import datetime

from .service import ServiceStubber


class LaunchConfigurationStubber(ServiceStubber):

    client_service = 'ec2'

    def add_describe_launch_configurations_empty_response(self):
        return self.add_response(
            'describe_launch_configurations',
            service_response={
                'LaunchConfigurations': [],
            },
            expected_params={},
        )

    def add_describe_launch_configurations_one_response(self):
        return self.add_response(
            'describe_launch_configurations',
            service_response={
                'LaunchConfigurations': [{
                    'LaunchConfigurationName': self.resource.name,
                    'ImageId': 'ami-cba130bc',
                    'InstanceType': 't2.micro',
                    'CreatedTime': datetime.datetime.now(),
                }],
            },
            expected_params={},
        )

    def add_describe_auto_scaling_groups(self):
        return self.add_response(
            'describe_auto_scaling_groups',
            service_response={
                'AutoScalingGroups': [],
            },
            expected_params={},
        )

    def add_create_launch_configuration(self):
        return self.add_response(
            'create_launch_configuration',
            service_response={
            },
            expected_params={
                'ImageId': 'ami-cba130bc',
                'InstanceMonitoring': {'Enabled': False},
                'InstanceType': 't2.micro',
                'LaunchConfigurationName': 'my-test-lc.1'
            }
        )

    def add_delete_launch_configuration(self):
        return self.add_response(
            'delete_launch_configuration',
            service_response={
            },
            expected_params={
                'LaunchConfigurationName': self.resource.name,
            },
        )
