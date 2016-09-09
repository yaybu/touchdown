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
from touchdown.tests.stubs.aws import InstanceProfileStubber

from .fixtures.aws import RoleFixture


class TestCreateInstanceProfile(StubberTestCase):

    def test_create_instance_profile(self):
        goal = self.create_goal('apply')

        role = self.fixtures.enter_context(RoleFixture(goal, self.aws))

        instance_profile = self.fixtures.enter_context(InstanceProfileStubber(
            goal.get_service(
                self.aws.add_instance_profile(
                    name='my-test-profile',
                    roles=[role],
                ),
                'apply',
            )
        ))
        instance_profile.add_list_instance_profile_empty_response()
        instance_profile.add_create_instance_profile()
        instance_profile.add_add_role_to_instance_profile()

        goal.execute()

    def test_create_instance_profile_idempotent(self):
        goal = self.create_goal('apply')

        role = self.fixtures.enter_context(RoleFixture(goal, self.aws))

        instance_profile = self.fixtures.enter_context(InstanceProfileStubber(
            goal.get_service(
                self.aws.add_instance_profile(
                    name='my-test-profile',
                    roles=[role],
                ),
                'apply',
            )
        ))
        instance_profile.add_list_instance_profile_one_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(instance_profile.resource)), 0)


class TestDestroyInstanceProfile(StubberTestCase):

    def test_destroy_instance_profile(self):
        goal = self.create_goal('destroy')

        role = self.fixtures.enter_context(RoleFixture(goal, self.aws))

        instance_profile = self.fixtures.enter_context(InstanceProfileStubber(
            goal.get_service(
                self.aws.add_instance_profile(
                    name='my-test-profile',
                    roles=[role],
                ),
                'destroy',
            )
        ))
        instance_profile.add_list_instance_profile_one_response()
        instance_profile.add_remove_role_from_instance_profile()
        instance_profile.add_delete_instance_profile()

        goal.execute()

    def test_destroy_role_idempotent(self):
        goal = self.create_goal('destroy')

        instance_profile = self.fixtures.enter_context(InstanceProfileStubber(
            goal.get_service(
                self.aws.add_instance_profile(
                    name='my-test-profile',
                ),
                'destroy',
            )
        ))
        instance_profile.add_list_instance_profile_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(instance_profile.resource)), 0)
