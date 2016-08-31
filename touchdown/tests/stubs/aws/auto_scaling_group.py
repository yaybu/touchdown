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


class AutoScalingGroupStubber(ServiceStubber):

    client_service = 'ec2'

    def add_describe_auto_scaling_groups_empty_response(self):
        return self.add_response(
            'describe_auto_scaling_groups',
            service_response={
                'AutoScalingGroups': [],
            },
            expected_params={
                'AutoScalingGroupNames': [self.resource.name],
            },
        )

    def add_describe_auto_scaling_groups_one_response(self):
        return self.add_response(
            'describe_auto_scaling_groups',
            service_response={
                'AutoScalingGroups': [{
                    'AutoScalingGroupName': self.resource.name,
                    'LaunchConfigurationName': 'my-test-lc',
                    'MinSize': 0,
                    'MaxSize': 0,
                    'DesiredCapacity': 0,
                    'DefaultCooldown': 0,
                    'AvailabilityZones': ['eu-west-1a'],
                    'HealthCheckType': 'ELB',
                    'CreatedTime': datetime.datetime.now(),
                }],
            },
            expected_params={
                'AutoScalingGroupNames': [self.resource.name],
            },
        )

    def add_describe_scaling_activities(self, status_code='Successful'):
        return self.add_response(
            'describe_scaling_activities',
            service_response={
                'Activities': [{
                    'AutoScalingGroupName': self.resource.name,
                    'StatusCode': status_code,
                    'Cause': 'Requested by user',
                    'ActivityId': 'ZZZZ',
                    'StartTime': datetime.datetime.now(),
                }],
            },
            expected_params={
                'AutoScalingGroupName': self.resource.name,
            },
        )

    def add_create_auto_scaling_group(self):
        return self.add_response(
            'create_auto_scaling_group',
            service_response={
            },
            expected_params={
                'AutoScalingGroupName': 'my-asg',
                'LaunchConfigurationName': 'my-test-lc',
                'MinSize': 0,
                'MaxSize': 0,
                'DefaultCooldown': 300,
                'Tags': [],
                'TerminationPolicies': ['Default'],
            }
        )

    def add_update_auto_scaling_group_SCALEDOWN(self):
        return self.add_response(
            'update_auto_scaling_group',
            service_response={},
            expected_params={
                'AutoScalingGroupName': self.resource.name,
                'MinSize': 0,
                'MaxSize': 0,
                'DesiredCapacity': 0,
            }
        )

    def add_delete_auto_scaling_group(self):
        return self.add_response(
            'delete_auto_scaling_group',
            service_response={
            },
            expected_params={
                'AutoScalingGroupName': self.resource.name,
            },
        )
