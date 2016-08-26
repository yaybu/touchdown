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
from touchdown.tests.stubs.aws import TopicStubber


class TestTopicCreation(StubberTestCase):

    def test_create_topic(self):
        goal = self.create_goal('apply')

        topic = self.fixtures.enter_context(TopicStubber(
            goal.get_service(
                self.aws.add_topic(
                    name='test-topic',
                ),
                'apply',
            )
        ))

        topic.add_list_topics_empty_response()
        topic.add_create_topic()
        topic.add_list_topics_one_response()
        topic.add_list_topics_one_response()

        goal.execute()

    def test_create_topic_idempotent(self):
        goal = self.create_goal('apply')

        topic = self.fixtures.enter_context(TopicStubber(
            goal.get_service(
                self.aws.add_topic(
                    name='test-topic',
                ),
                'apply',
            )
        ))

        topic.add_list_topics_one_response()
        topic.add_list_subscriptions_by_topic()
        topic.add_get_topic_attributes()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(topic.resource)), 0)


class TestTopicDestroy(StubberTestCase):

    def test_destroy_topic(self):
        goal = self.create_goal('destroy')

        topic = self.fixtures.enter_context(TopicStubber(
            goal.get_service(
                self.aws.add_topic(
                    name='test-topic',
                ),
                'destroy',
            )
        ))

        topic.add_list_topics_one_response()
        topic.add_delete_topic()

        goal.execute()

    def test_destroy_topic_idempotent(self):
        goal = self.create_goal('destroy')

        topic = self.fixtures.enter_context(TopicStubber(
            goal.get_service(
                self.aws.add_topic(
                    name='test-topic',
                ),
                'destroy',
            )
        ))

        topic.add_list_topics_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(topic.resource)), 0)
