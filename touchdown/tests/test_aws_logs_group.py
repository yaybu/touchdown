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
from touchdown.tests.stubs.aws import LogGroupStubber


class TestLogGroupCreation(StubberTestCase):

    def test_create_log_group(self):
        goal = self.create_goal('apply')

        log_group = self.fixtures.enter_context(LogGroupStubber(
            goal.get_service(
                self.aws.add_log_group(
                    name='test-log_group',
                ),
                'apply',
            )
        ))

        log_group.add_describe_log_groups_empty_response()
        log_group.add_create_log_group()
        log_group.add_describe_log_groups_one_response()
        log_group.add_describe_log_groups_one_response()
        log_group.add_describe_log_groups_one_response()

        goal.execute()

    def test_update_log_group_retention(self):
        goal = self.create_goal('apply')

        log_group = self.fixtures.enter_context(LogGroupStubber(
            goal.get_service(
                self.aws.add_log_group(
                    name='test-log_group',
                    retention=7,
                ),
                'apply',
            )
        ))

        log_group.add_describe_log_groups_one_response()
        log_group.add_put_retention_policy(7)

        goal.execute()

    def test_create_log_group_idempotent(self):
        goal = self.create_goal('apply')

        log_group = self.fixtures.enter_context(LogGroupStubber(
            goal.get_service(
                self.aws.add_log_group(
                    name='test-log_group',
                ),
                'apply',
            )
        ))

        log_group.add_describe_log_groups_one_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(log_group.resource)), 0)


class TestLogGroupDestroy(StubberTestCase):

    def test_destroy_log_group(self):
        goal = self.create_goal('destroy')

        log_group = self.fixtures.enter_context(LogGroupStubber(
            goal.get_service(
                self.aws.add_log_group(
                    name='test-log_group',
                ),
                'destroy',
            )
        ))

        log_group.add_describe_log_groups_one_response()
        log_group.add_delete_log_group()

        goal.execute()

    def test_destroy_log_group_idempotent(self):
        goal = self.create_goal('destroy')

        log_group = self.fixtures.enter_context(LogGroupStubber(
            goal.get_service(
                self.aws.add_log_group(
                    name='test-log_group',
                ),
                'destroy',
            )
        ))

        log_group.add_describe_log_groups_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(log_group.resource)), 0)
