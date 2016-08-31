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
from touchdown.tests.stubs.aws import KeyStubber


class TestKeyCreation(StubberTestCase):

    def test_create_key(self):
        goal = self.create_goal('apply')

        key = self.fixtures.enter_context(KeyStubber(
            goal.get_service(
                self.aws.add_key(
                    name='test-key',
                ),
                'apply',
            )
        ))

        key.add_list_keys_empty()
        key.add_create_key()

        goal.execute()

    def test_create_key_idempotent(self):
        goal = self.create_goal('apply')

        key = self.fixtures.enter_context(KeyStubber(
            goal.get_service(
                self.aws.add_key(
                    name='test-key',
                ),
                'apply',
            )
        ))

        key.add_list_keys_one()
        key.add_describe_key()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(key.resource)), 0)


class TestKeyDestroy(StubberTestCase):

    def test_destroy_key(self):
        goal = self.create_goal('destroy')

        key = self.fixtures.enter_context(KeyStubber(
            goal.get_service(
                self.aws.add_key(
                    name='test-key',
                ),
                'destroy',
            )
        ))

        key.add_list_keys_one()
        key.add_describe_key()
        key.add_schedule_key_deletion()

        goal.execute()

    def test_destroy_key_idempotent(self):
        goal = self.create_goal('destroy')

        key = self.fixtures.enter_context(KeyStubber(
            goal.get_service(
                self.aws.add_key(
                    name='test-key',
                ),
                'destroy',
            )
        ))

        key.add_list_keys_empty()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(key.resource)), 0)
