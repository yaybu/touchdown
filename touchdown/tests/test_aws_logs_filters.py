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
from touchdown.tests.stubs.aws import LogFilterStubber, LogGroupStubber


class TestCreateLogFilter(StubberTestCase):

    def test_create_log_filter(self):
        goal = self.create_goal('apply')

        log_group = self.fixtures.enter_context(LogGroupStubber(
            goal.get_service(
                self.aws.add_log_group(
                    name='test-log-group',
                ),
                'apply',
            )
        ))
        log_group.add_describe_log_groups_one_response()

        log_filter = self.fixtures.enter_context(LogFilterStubber(
            goal.get_service(
                log_group.resource.add_filter(
                    name='test-log-filter',
                    pattern='pattern',
                    transformations=[{
                        'name': 'transformation-name',
                        'namespace': 'transformation-namespace',
                        'value': 'transformation-value',
                    }],
                ),
                'apply',
            )
        ))
        log_filter.add_describe_log_filter_empty_response()
        log_filter.add_create_log_filter()
        log_filter.add_describe_log_filter_one_response()
        log_filter.add_describe_log_filter_one_response()
        log_filter.add_describe_log_filter_one_response()

        goal.execute()

    def test_create_log_filter_idempotent(self):
        goal = self.create_goal('apply')

        log_group = self.fixtures.enter_context(LogGroupStubber(
            goal.get_service(
                self.aws.add_log_group(
                    name='test-log-group',
                ),
                'apply',
            )
        ))
        log_group.add_describe_log_groups_one_response()

        log_filter = self.fixtures.enter_context(LogFilterStubber(
            goal.get_service(
                log_group.resource.add_filter(
                    name='test-log-filter',
                    pattern='pattern',
                    transformations=[{
                        'name': 'transformation-name',
                        'namespace': 'transformation-namespace',
                        'value': 'transformation-value',
                    }],
                ),
                'apply',
            )
        ))
        log_filter.add_describe_log_filter_one_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(log_filter.resource)), 0)


class TestDestroyLogFilter(StubberTestCase):

    def test_destroy_log_filter(self):
        goal = self.create_goal('destroy')

        log_group = self.fixtures.enter_context(LogGroupStubber(
            goal.get_service(
                self.aws.get_log_group(
                    name='test-log-group',
                ),
                'describe',
            ),
        ))
        log_group.add_describe_log_groups_one_response()

        log_filter = self.fixtures.enter_context(LogFilterStubber(
            goal.get_service(
                log_group.resource.add_filter(
                    name='test-log-filter',
                ),
                'destroy',
            )
        ))
        log_filter.add_describe_log_filter_one_response()
        log_filter.add_delete_log_filter()

        goal.execute()

    def test_destroy_log_filter_idempotent(self):
        goal = self.create_goal('destroy')

        log_group = self.fixtures.enter_context(LogGroupStubber(
            goal.get_service(
                self.aws.get_log_group(
                    name='test-log-group',
                ),
                'describe',
            ),
        ))
        log_group.add_describe_log_groups_one_response()

        log_filter = self.fixtures.enter_context(LogFilterStubber(
            goal.get_service(
                log_group.resource.add_filter(
                    name='test-log-filter',
                ),
                'destroy',
            )
        ))
        log_filter.add_describe_log_filter_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(log_filter.resource)), 0)
