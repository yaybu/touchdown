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
from touchdown.tests.stubs.aws import EventRuleStubber


class TestRuleDeletion(StubberTestCase):

    def test_delete_rule(self):
        goal = self.create_goal('destroy')

        rule = self.fixtures.enter_context(EventRuleStubber(
            goal.get_service(
                self.aws.add_event_rule(
                    name='my-rule',
                ),
                'destroy',
            )
        ))
        rule.add_list_rules_one_response_by_name()
        rule.add_list_targets_by_rule([
            {'Id': 'SomeTargetId', 'Arn': 'some:arn:12345'},
            {'Id': 'SomeTargetId2', 'Arn': 'some:arn:12345'},
        ])
        rule.add_remove_targets(['SomeTargetId'])
        rule.add_remove_targets(['SomeTargetId2'])
        rule.add_delete_rule()

        goal.execute()

    def test_delete_rule_idempotent(self):
        goal = self.create_goal('destroy')

        rule = self.fixtures.enter_context(EventRuleStubber(
            goal.get_service(
                self.aws.add_event_rule(
                    name='my-rule',
                ),
                'destroy',
            )
        ))
        rule.add_list_rules_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(rule.resource)), 0)
