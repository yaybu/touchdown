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
from touchdown.tests.stubs.aws import PasswordPolicyStubber


class TestPasswordPolicyCreation(StubberTestCase):

    def test_create_password_policy(self):
        goal = self.create_goal('apply')

        password_policy = self.fixtures.enter_context(PasswordPolicyStubber(
            goal.get_service(
                self.aws.add_password_policy(
                    allow_users_to_change_password=False,
                ),
                'apply',
            )
        ))
        password_policy.add_get_account_password_policy_empty_response()
        password_policy.add_update_account_password_policy(
            AllowUsersToChangePassword=False,
        )
        password_policy.add_get_account_password_policy()
        password_policy.add_get_account_password_policy()
        password_policy.add_get_account_password_policy()

        goal.execute()

    def test_create_password_policy_idempotent(self):
        goal = self.create_goal('apply')

        password_policy = self.fixtures.enter_context(PasswordPolicyStubber(
            goal.get_service(
                self.aws.add_password_policy(
                ),
                'apply',
            )
        ))
        password_policy.add_get_account_password_policy()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(password_policy.resource)), 0)

    def test_update_password_policy(self):
        goal = self.create_goal('apply')

        password_policy = self.fixtures.enter_context(PasswordPolicyStubber(
            goal.get_service(
                self.aws.add_password_policy(
                    allow_users_to_change_password=True,
                ),
                'apply',
            )
        ))
        password_policy.add_get_account_password_policy()
        password_policy.add_update_account_password_policy(
            AllowUsersToChangePassword=True,
        )
        goal.execute()


class TestPasswordPolicyDeletion(StubberTestCase):

    def test_delete_password_policy(self):
        goal = self.create_goal('destroy')

        password_policy = self.fixtures.enter_context(PasswordPolicyStubber(
            goal.get_service(
                self.aws.add_password_policy(
                ),
                'destroy',
            )
        ))
        password_policy.add_get_account_password_policy()
        password_policy.add_delete_account_password_policy()

        goal.execute()

    def test_delete_password_policy_idempotent(self):
        goal = self.create_goal('destroy')

        password_policy = self.fixtures.enter_context(PasswordPolicyStubber(
            goal.get_service(
                self.aws.add_password_policy(
                ),
                'destroy',
            )
        ))
        password_policy.add_get_account_password_policy_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(password_policy.resource)), 0)
