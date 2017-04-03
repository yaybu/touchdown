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

from touchdown.tests.aws import StubberTestCase
from touchdown.tests.stubs.aws import EC2InstanceStubber
from .fixtures.aws import InstanceProfileFixture


class TestInstanceCreation(StubberTestCase):

    def test_create_instance(self):
        goal = self.create_goal('apply')

        instance = self.fixtures.enter_context(EC2InstanceStubber(
            goal.get_service(
                self.aws.add_ec2_instance(
                    name='my-ec2-instance',
                    ami='foobarbaz',
                ),
                'apply',
            )
        ))

        instance.add_describe_instances_empty_response_by_name()
        instance.add_run_instance()
        instance.add_create_tags(Name='my-ec2-instance')

        # Test that it waits for the instance to be available
        instance.add_describe_instances_empty_response_by_name()
        instance.add_describe_instances_empty_response_by_name()
        instance.add_describe_instances_one_response_by_name()

        # And then it will refresh its metadata
        instance.add_describe_instances_one_response_by_name()

        goal.execute()

    def test_create_instance_idempotent(self):
        goal = self.create_goal('apply')

        instance = self.fixtures.enter_context(EC2InstanceStubber(
            goal.get_service(
                self.aws.add_ec2_instance(
                    name='my-ec2-instance',
                ),
                'apply',
            )
        ))
        instance.add_describe_instances_one_response_by_name()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(instance.resource)), 0)

    def test_create_instance_with_profile(self):
        goal = self.create_goal('apply')

        instance_profile = self.fixtures.enter_context(InstanceProfileFixture(goal, self.aws))

        instance = self.fixtures.enter_context(EC2InstanceStubber(
            goal.get_service(
                self.aws.add_ec2_instance(
                    name='my-ec2-instance',
                    ami='foobarbaz',
                    instance_profile=instance_profile,
                ),
                'apply',
            )
        ))

        instance.add_describe_instances_empty_response_by_name()
        instance.add_run_instance_with_profile()
        instance.add_create_tags(Name='my-ec2-instance')

        # Test that it waits for the instance to be available
        instance.add_describe_instances_empty_response_by_name()
        instance.add_describe_instances_empty_response_by_name()
        instance.add_describe_instances_one_response_by_name()

        # And then it will refresh its metadata
        instance.add_describe_instances_one_response_by_name()

        goal.execute()


class TestInstanceDeletion(StubberTestCase):

    def test_delete_instance(self):
        goal = self.create_goal('destroy')

        instance = self.fixtures.enter_context(EC2InstanceStubber(
            goal.get_service(
                self.aws.add_ec2_instance(
                    name='my-ec2-instance',
                ),
                'destroy',
            )
        ))
        instance.add_describe_instances_one_response_by_name()
        instance.add_terminate_instances()

        # Test that it waits for the instance to be gone
        instance.add_describe_instances_one_response_by_name(state='shutting-down')
        instance.add_describe_instances_one_response_by_name(state='shutting-down')
        instance.add_describe_instances_empty_response_by_name()

        goal.execute()

    def test_delete_instance_idempotent(self):
        goal = self.create_goal('destroy')

        instance = self.fixtures.enter_context(EC2InstanceStubber(
            goal.get_service(
                self.aws.add_ec2_instance(
                    name='my-ec2-instance',
                ),
                'destroy',
            )
        ))
        instance.add_describe_instances_empty_response_by_name()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(instance.resource)), 0)
