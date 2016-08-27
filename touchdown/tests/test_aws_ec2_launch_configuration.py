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
from touchdown.tests.stubs.aws import LaunchConfigurationStubber


class TestCreateLaunchConfiguration(StubberTestCase):

    def test_create_launch_config(self):
        goal = self.create_goal('apply')

        launch_config = self.fixtures.enter_context(LaunchConfigurationStubber(
            goal.get_service(
                self.aws.add_launch_configuration(
                    name='my-test-lc',
                    image='ami-cba130bc',
                    instance_type='t2.micro',
                ),
                'apply',
            )
        ))

        launch_config.add_describe_launch_configurations_empty_response()
        launch_config.add_describe_launch_configurations_empty_response()
        launch_config.add_create_launch_configuration()
        launch_config.add_describe_launch_configurations_one_response()
        launch_config.add_describe_launch_configurations_one_response()
        launch_config.add_describe_launch_configurations_one_response()
        goal.execute()

    def test_create_launch_config_idempotent(self):
        goal = self.create_goal('apply')

        launch_config = self.fixtures.enter_context(LaunchConfigurationStubber(
            goal.get_service(
                self.aws.add_launch_configuration(
                    name='my-test-lc',
                    image='ami-cba130bc',
                    instance_type='t2.micro',
                ),
                'apply',
            )
        ))

        launch_config.add_describe_launch_configurations_one_response()
        launch_config.add_describe_launch_configurations_one_response()
        launch_config.add_describe_auto_scaling_groups()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(launch_config.resource)), 0)


class TestDestroyLaunchConfiguration(StubberTestCase):

    def test_destroy_launch_config(self):
        goal = self.create_goal('destroy')

        launch_config = self.fixtures.enter_context(LaunchConfigurationStubber(
            goal.get_service(
                self.aws.add_launch_configuration(
                    name='my-test-lc',
                    image='ami-cba130bc',
                    instance_type='t2.micro',
                ),
                'destroy',
            )
        ))

        launch_config.add_describe_launch_configurations_one_response()
        launch_config.add_describe_launch_configurations_one_response()
        launch_config.add_delete_launch_configuration()

        goal.execute()

    def test_destroy_launch_config_idempotent(self):
        goal = self.create_goal('destroy')

        launch_config = self.fixtures.enter_context(LaunchConfigurationStubber(
            goal.get_service(
                self.aws.add_launch_configuration(
                    name='my-test-lc',
                    image='ami-cba130bc',
                    instance_type='t2.micro',
                ),
                'destroy',
            )
        ))

        launch_config.add_describe_launch_configurations_empty_response()
        launch_config.add_describe_launch_configurations_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(launch_config.resource)), 0)
