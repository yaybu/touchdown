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

    def build_instances(self, instances):
        retval = []
        for row in instances:
            instance = {
                'InstanceId': 'i-abcd1234',
                'AvailabilityZone': 'eu-west-1a',
                'HealthStatus': 'Healthy',
                'LaunchConfigurationName': 'old-launch-config',
                'ProtectedFromScaleIn': True,
            }
            instance.update(row)
            retval.append(instance)
        return retval

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

    def add_describe_auto_scaling_groups_one_response(self, min_size=0, max_size=0, instances=None):
        return self.add_response(
            'describe_auto_scaling_groups',
            service_response={
                'AutoScalingGroups': [{
                    'AutoScalingGroupName': self.resource.name,
                    'LaunchConfigurationName': 'my-test-lc',
                    'MinSize': min_size,
                    'MaxSize': max_size,
                    'DesiredCapacity': 0,
                    'DefaultCooldown': 0,
                    'AvailabilityZones': ['eu-west-1a'],
                    'HealthCheckType': 'ELB',
                    'CreatedTime': datetime.datetime.now(),
                    'Instances': self.build_instances(instances or []),
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

    def add_create_auto_scaling_group(self, min_size=0, max_size=0):
        return self.add_response(
            'create_auto_scaling_group',
            service_response={
            },
            expected_params={
                'AutoScalingGroupName': 'my-asg',
                'LaunchConfigurationName': 'my-test-lc',
                'MinSize': min_size,
                'MaxSize': max_size,
                'DefaultCooldown': 300,
                'Tags': [],
                'TerminationPolicies': ['Default'],
            }
        )

    def add_update_auto_scaling_group(self, desired=None, min=None, max=None):
        params = {
            'AutoScalingGroupName': self.resource.name,
        }
        if desired is not None:
            params['DesiredCapacity'] = desired
        if min is not None:
            params['MinSize'] = min
        if max is not None:
            params['MaxSize'] = max
        return self.add_response(
            'update_auto_scaling_group',
            service_response={},
            expected_params=params,
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

    def add_suspend_processes(self):
        return self.add_response(
            'suspend_processes',
            service_response={
            },
            expected_params={
                'AutoScalingGroupName': self.resource.name,
                'ScalingProcesses': [
                    'AlarmNotification',
                    'AZRebalance',
                    'ReplaceUnhealthy',
                    'ScheduledActions',
                ],
            },
        )

    def add_resume_processes(self):
        return self.add_response(
            'resume_processes',
            service_response={
            },
            expected_params={
                'AutoScalingGroupName': self.resource.name,
                'ScalingProcesses': [
                    'AlarmNotification',
                    'AZRebalance',
                    'ReplaceUnhealthy',
                    'ScheduledActions',
                ],
            },
        )
