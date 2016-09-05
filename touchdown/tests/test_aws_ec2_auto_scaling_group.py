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

from touchdown.tests.aws import StubberTestCase
from touchdown.tests.fixtures.aws import LaunchConfigurationFixture
from touchdown.tests.stubs.aws import AutoScalingGroupStubber


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

        auto_scaling_group.add_describe_auto_scaling_groups_one_response()

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
