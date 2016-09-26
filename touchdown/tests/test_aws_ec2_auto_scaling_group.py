# Copyright 2015 Isotoma Limited
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

from touchdown.core import errors
from touchdown.tests.aws import Stubber, StubberTestCase
from touchdown.tests.fixtures.aws import LaunchConfigurationFixture
from touchdown.tests.stubs.aws import (
    AutoScalingGroupStubber,
    EC2InstanceStubber,
)


class TestCreateAutoScalingGroupuration(StubberTestCase):

    def test_create_auto_scaling_group(self):
        goal = self.create_goal('apply')

        launch_config = self.fixtures.enter_context(LaunchConfigurationFixture(goal, self.aws))

        auto_scaling_group = self.fixtures.enter_context(AutoScalingGroupStubber(
            goal.get_service(
                self.aws.add_auto_scaling_group(
                    name='my-asg',
                    min_size=0,
                    max_size=0,
                    launch_configuration=launch_config,
                ),
                'apply',
            )
        ))

        auto_scaling_group.add_describe_auto_scaling_groups_empty_response()
        auto_scaling_group.add_create_auto_scaling_group()
        auto_scaling_group.add_describe_auto_scaling_groups_one_response()
        auto_scaling_group.add_describe_auto_scaling_groups_one_response()
        auto_scaling_group.add_describe_auto_scaling_groups_one_response()
        goal.execute()

    def test_create_auto_scaling_group_wait_for_healthy(self):
        goal = self.create_goal('apply')

        launch_config = self.fixtures.enter_context(LaunchConfigurationFixture(goal, self.aws))

        auto_scaling_group = self.fixtures.enter_context(AutoScalingGroupStubber(
            goal.get_service(
                self.aws.add_auto_scaling_group(
                    name='my-asg',
                    min_size=1,
                    max_size=1,
                    launch_configuration=launch_config,
                ),
                'apply',
            )
        ))

        auto_scaling_group.add_describe_auto_scaling_groups_empty_response()
        auto_scaling_group.add_create_auto_scaling_group(
            min_size=1,
            max_size=1,
        )
        auto_scaling_group.add_describe_auto_scaling_groups_one_response()
        auto_scaling_group.add_describe_auto_scaling_groups_one_response()
        auto_scaling_group.add_describe_auto_scaling_groups_one_response()

        # Now wait for an ec2 instance to be in a healthy state
        # First of all lets mock one starting...
        auto_scaling_group.add_describe_auto_scaling_groups_one_response(
            instances=[{'LifecycleState': 'Pending'}],
        )

        # And now its ready...
        auto_scaling_group.add_describe_auto_scaling_groups_one_response(
            instances=[{'LifecycleState': 'InService'}],
        )

        goal.execute()

    def test_update_auto_scaling_group_replace_instances(self):
        goal = self.create_goal('apply')

        launch_config = self.fixtures.enter_context(LaunchConfigurationFixture(goal, self.aws))

        auto_scaling_group = self.fixtures.enter_context(AutoScalingGroupStubber(
            goal.get_service(
                self.aws.add_auto_scaling_group(
                    name='my-asg',
                    min_size=1,
                    max_size=1,
                    launch_configuration=launch_config,
                ),
                'apply',
            )
        ))

        auto_scaling_group.add_describe_auto_scaling_groups_one_response(
            min_size=1,
            max_size=1,
            instances=[
                # This one should be ignored
                {'LifecycleState': 'Terminating'},
                # This one should be removed
                {'LifecycleState': 'InService'},
            ],
        )

        auto_scaling_group.add_suspend_processes()

        auto_scaling_group.add_update_auto_scaling_group(desired=1, max=1)
        auto_scaling_group.add_describe_auto_scaling_groups_one_response(
            min_size=1,
            max_size=1,
            instances=[
                # This one should be removed
                {'LifecycleState': 'InService'},
            ],
        )

        auto_scaling_group.add_response(
            'terminate_instance_in_auto_scaling_group',
            service_response={},
            expected_params={
                'InstanceId': 'i-abcd1234',
                'ShouldDecrementDesiredCapacity': False,
            },
        )
        auto_scaling_group.add_describe_auto_scaling_groups_one_response(
            min_size=1,
            max_size=1,
            instances=[
                {'LifecycleState': 'InService'},
            ],
        )

        # GracefulReplacement.unscale
        auto_scaling_group.add_update_auto_scaling_group(desired=0, max=1)
        auto_scaling_group.add_describe_auto_scaling_groups_one_response(
            min_size=1,
            max_size=1,
            instances=[],
        )

        # GracefulReplacement.run -'Resuming autoscaling activities'
        auto_scaling_group.add_resume_processes()

        # Set self.plan.object before returning control
        auto_scaling_group.add_describe_auto_scaling_groups_one_response()

        goal.execute()

    def test_create_auto_scaling_group_idempotent(self):
        goal = self.create_goal('apply')

        launch_config = self.fixtures.enter_context(LaunchConfigurationFixture(goal, self.aws))

        auto_scaling_group = self.fixtures.enter_context(AutoScalingGroupStubber(
            goal.get_service(
                self.aws.add_auto_scaling_group(
                    name='my-asg',
                    min_size=0,
                    max_size=0,
                    launch_configuration=launch_config,
                ),
                'apply',
            )
        ))

        auto_scaling_group.add_describe_auto_scaling_groups_one_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(auto_scaling_group.resource)), 0)


class TestDestroyAutoScalingGroupuration(StubberTestCase):

    def test_destroy_auto_scaling_group(self):
        goal = self.create_goal('destroy')

        auto_scaling_group = self.fixtures.enter_context(AutoScalingGroupStubber(
            goal.get_service(
                self.aws.add_auto_scaling_group(
                    name='my-asg',
                    min_size=0,
                    max_size=0,
                ),
                'destroy',
            )
        ))

        # Test stopping an ASG that has instances running
        auto_scaling_group.add_describe_auto_scaling_groups_one_response(
            instances=[{'LifecycleState': 'InService'}],
        )

        # Scale the ASG down to 0 (min, max and desired)
        auto_scaling_group.add_update_auto_scaling_group_SCALEDOWN()

        # It waits for describe_auto_scaling_groups().Instances to be []
        auto_scaling_group.add_describe_auto_scaling_groups_one_response(
            instances=[{'LifecycleState': 'InService'}],
        )
        auto_scaling_group.add_describe_auto_scaling_groups_one_response()

        # Make sure there are no activities in progress
        auto_scaling_group.add_describe_scaling_activities(status_code='InProgress')
        auto_scaling_group.add_describe_scaling_activities(status_code='Successful')

        # Now we can actually delete it
        auto_scaling_group.add_delete_auto_scaling_group()

        goal.execute()

    def test_destroy_auto_scaling_group_idempotent(self):
        goal = self.create_goal('destroy')

        auto_scaling_group = self.fixtures.enter_context(AutoScalingGroupStubber(
            goal.get_service(
                self.aws.add_auto_scaling_group(
                    name='my-asg',
                    min_size=0,
                    max_size=0,
                ),
                'destroy',
            )
        ))

        auto_scaling_group.add_describe_auto_scaling_groups_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(auto_scaling_group.resource)), 0)


class TestSshAutoScalingGroup(StubberTestCase):

    def test_ssh_auto_scaling_group_no_instances(self):
        goal = self.create_goal('ssh')

        auto_scaling_group = self.fixtures.enter_context(AutoScalingGroupStubber(
            goal.get_service(
                self.aws.get_auto_scaling_group(
                    name='my-asg',
                ),
                'describe',
            )
        ))
        auto_scaling_group.add_describe_auto_scaling_groups_one_response(
            instances=[]
        )

        ssh_connection = goal.get_service(
            self.workspace.add_ssh_connection(
                name='my-ssh-connection',
                instance=auto_scaling_group.resource,
                username='root',
                password='password',
            ),
            'ssh',
        )

        self.assertRaises(errors.ServiceNotReady, ssh_connection.get_command_and_args)

    def test_ssh_auto_scaling_group_no_instances_in_service(self):
        goal = self.create_goal('ssh')

        auto_scaling_group = self.fixtures.enter_context(AutoScalingGroupStubber(
            goal.get_service(
                self.aws.get_auto_scaling_group(
                    name='my-asg',
                ),
                'describe',
            )
        ))
        auto_scaling_group.add_describe_auto_scaling_groups_one_response(
            instances=[{
                'LifecycleState': 'Terminating',
            }]
        )

        ssh_connection = goal.get_service(
            self.workspace.add_ssh_connection(
                name='my-ssh-connection',
                instance=auto_scaling_group.resource,
                username='root',
                password='password',
            ),
            'ssh',
        )

        self.assertRaises(errors.ServiceNotReady, ssh_connection.get_command_and_args)

    def test_ssh_auto_scaling_group_instances_not_found_in_ec2(self):
        goal = self.create_goal('ssh')

        auto_scaling_group = self.fixtures.enter_context(AutoScalingGroupStubber(
            goal.get_service(
                self.aws.get_auto_scaling_group(
                    name='my-asg',
                ),
                'describe',
            )
        ))
        auto_scaling_group.add_describe_auto_scaling_groups_one_response(
            instances=[{
                'LifecycleState': 'InService',
                'InstanceId': 'i-abcde23f',
            }]
        )

        ec2_client_stub = self.fixtures.enter_context(Stubber(
            auto_scaling_group.service.ec2_client
        ))
        ec2_client_stub.add_response(
            'describe_instances',
            service_response={
                'Reservations': [],
            },
            expected_params={
                'InstanceIds': ['i-abcde23f']
            },
        )

        ssh_connection = goal.get_service(
            self.workspace.add_ssh_connection(
                name='my-ssh-connection',
                instance=auto_scaling_group.resource,
                username='root',
                password='password',
            ),
            'ssh',
        )

        self.assertRaises(errors.ServiceNotReady, ssh_connection.get_command_and_args)

    def test_ssh_auto_scaling_group_direct(self):
        goal = self.create_goal('ssh')

        auto_scaling_group = self.fixtures.enter_context(AutoScalingGroupStubber(
            goal.get_service(
                self.aws.get_auto_scaling_group(
                    name='my-asg',
                ),
                'describe',
            )
        ))
        auto_scaling_group.add_describe_auto_scaling_groups_one_response(
            instances=[{
                'LifecycleState': 'InService',
                'InstanceId': 'i-abcde23f',
            }]
        )

        ec2_client_stub = self.fixtures.enter_context(Stubber(
            auto_scaling_group.service.ec2_client
        ))
        ec2_client_stub.add_response(
            'describe_instances',
            service_response={
                'Reservations': [{
                    'Instances': [{
                        'PublicIpAddress': '8.8.8.8',
                    }]
                }]
            },
            expected_params={
                'InstanceIds': ['i-abcde23f']
            },
        )

        ssh_connection = goal.get_service(
            self.workspace.add_ssh_connection(
                name='my-ssh-connection',
                instance=auto_scaling_group.resource,
                username='root',
                password='password',
            ),
            'ssh',
        )

        self.assertEqual(ssh_connection.get_command(), '/usr/bin/ssh')
        self.assertEqual(ssh_connection.get_command_and_args(), [
            '/usr/bin/ssh',
            '-o', 'User="root"',
            '-o', 'Port="22"',
            '-o', 'HostName="8.8.8.8"',
            'remote',
        ])

    def test_ssh_auto_scaling_group_via_auto_scaling_group(self):
        # In this scenario there are 2 ASG's. One is public and one is not. They
        # both have SSH conenctions associated with them, and the private
        # ssh_connection has a proxy attribute set to the public ssh_connection.
        # `touchdown ssh` for the private connection should use -o ProxyCommand
        # to bounce off the public host.
        goal = self.create_goal('ssh')

        auto_scaling_group = self.fixtures.enter_context(AutoScalingGroupStubber(
            goal.get_service(
                self.aws.get_auto_scaling_group(
                    name='my-asg',
                ),
                'describe',
            )
        ))
        auto_scaling_group.add_describe_auto_scaling_groups_one_response(
            instances=[{
                'LifecycleState': 'InService',
                'InstanceId': 'i-abcde23f',
            }]
        )
        auto_scaling_group.add_describe_auto_scaling_groups_one_response(
            instances=[{
                'LifecycleState': 'InService',
                'InstanceId': 'i-abcde23f',
            }]
        )

        ec2_client_stub = self.fixtures.enter_context(Stubber(
            auto_scaling_group.service.ec2_client
        ))
        ec2_client_stub.add_response(
            'describe_instances',
            service_response={
                'Reservations': [{
                    'Instances': [{
                        'PublicIpAddress': '8.8.8.8',
                        'VpcId': 'vpc-de3db33',
                    }]
                }]
            },
            expected_params={
                'InstanceIds': ['i-abcde23f']
            },
        )
        ec2_client_stub.add_response(
            'describe_instances',
            service_response={
                'Reservations': [{
                    'Instances': [{
                        'PublicIpAddress': '8.8.8.8',
                        'VpcId': 'vpc-de3db33',
                    }]
                }]
            },
            expected_params={
                'InstanceIds': ['i-abcde23f']
            },
        )

        ssh_connection = goal.get_service(
            self.workspace.add_ssh_connection(
                name='my-ssh-connection',
                instance=auto_scaling_group.resource,
                username='root',
                password='password',
            ),
            'ssh',
        )

        auto_scaling_group2 = self.fixtures.enter_context(AutoScalingGroupStubber(
            goal.get_service(
                self.aws.get_auto_scaling_group(
                    name='my-asg-2',
                ),
                'describe',
            )
        ))
        auto_scaling_group2.add_describe_auto_scaling_groups_one_response(
            instances=[{
                'LifecycleState': 'InService',
                'InstanceId': 'i-abcde23g',
            }]
        )

        ec2_client_stub2 = self.fixtures.enter_context(Stubber(
            auto_scaling_group2.service.ec2_client
        ))
        ec2_client_stub2.add_response(
            'describe_instances',
            service_response={
                'Reservations': [{
                    'Instances': [{
                        'PrivateIpAddress': '10.0.0.1',
                        'VpcId': 'vpc-de3db33',
                    }]
                }]
            },
            expected_params={
                'InstanceIds': ['i-abcde23g']
            },
        )

        ssh_connection_2 = goal.get_service(
            self.workspace.add_ssh_connection(
                name='my-ssh-connection',
                instance=auto_scaling_group2.resource,
                username='root',
                password='password',
                proxy=ssh_connection.resource,
            ),
            'ssh',
        )

        self.assertEqual(ssh_connection_2.get_command_and_args(), [
            '/usr/bin/ssh',
            '-o', 'User="root"',
            '-o', 'Port="22"',
            '-o', 'HostName="10.0.0.1"',
            '-o', 'ProxyCommand=/usr/bin/ssh -o User="root" -o Port="22" -W %h:%p 8.8.8.8',
            'remote',
        ])

    def test_ssh_ec2_instance_via_auto_scaling_group(self):
        # Private ec2 instance and public asg. Ec2 instance has an ssh_connection that proxies via the public asg ssh_connection

        # In this scenario there are 2 ASG's. One is public and one is not. They
        # both have SSH conenctions associated with them, and the private
        # ssh_connection has a proxy attribute set to the public ssh_connection.
        # `touchdown ssh` for the private connection should use -o ProxyCommand
        # to bounce off the public host.
        goal = self.create_goal('ssh')

        auto_scaling_group = self.fixtures.enter_context(AutoScalingGroupStubber(
            goal.get_service(
                self.aws.get_auto_scaling_group(
                    name='my-asg',
                ),
                'describe',
            )
        ))
        auto_scaling_group.add_describe_auto_scaling_groups_one_response(
            instances=[{
                'LifecycleState': 'InService',
                'InstanceId': 'i-abcde23f',
            }]
        )
        auto_scaling_group.add_describe_auto_scaling_groups_one_response(
            instances=[{
                'LifecycleState': 'InService',
                'InstanceId': 'i-abcde23f',
            }]
        )

        ec2_client_stub = self.fixtures.enter_context(Stubber(
            auto_scaling_group.service.ec2_client
        ))
        ec2_client_stub.add_response(
            'describe_instances',
            service_response={
                'Reservations': [{
                    'Instances': [{
                        'PublicIpAddress': '8.8.8.8',
                        'VpcId': 'vpc-de3db33',
                    }]
                }]
            },
            expected_params={
                'InstanceIds': ['i-abcde23f']
            },
        )
        ec2_client_stub.add_response(
            'describe_instances',
            service_response={
                'Reservations': [{
                    'Instances': [{
                        'PublicIpAddress': '8.8.8.8',
                        'VpcId': 'vpc-de3db33',
                    }]
                }]
            },
            expected_params={
                'InstanceIds': ['i-abcde23f']
            },
        )

        ssh_connection = goal.get_service(
            self.workspace.add_ssh_connection(
                name='my-ssh-connection',
                instance=auto_scaling_group.resource,
                username='root',
                password='password',
            ),
            'ssh',
        )

        ec2_instance = self.fixtures.enter_context(EC2InstanceStubber(
            goal.get_service(
                self.aws.get_ec2_instance(
                    name='my-ec2-instance',
                ),
                'describe',
            )
        ))
        ec2_instance.add_describe_instances_one_response_by_name()
        ec2_instance.add_describe_instances_one_response_by_name()

        ssh_connection_2 = goal.get_service(
            self.workspace.add_ssh_connection(
                name='my-ssh-connection',
                instance=ec2_instance.resource,
                username='root',
                password='password',
                proxy=ssh_connection.resource,
            ),
            'ssh',
        )

        self.assertEqual(ssh_connection_2.get_command_and_args(), [
            '/usr/bin/ssh',
            '-o', 'User="root"',
            '-o', 'Port="22"',
            '-o', 'HostName="10.0.0.42"',
            '-o', 'ProxyCommand=/usr/bin/ssh -o User="root" -o Port="22" -W %h:%p 8.8.8.8',
            'remote',
        ])
