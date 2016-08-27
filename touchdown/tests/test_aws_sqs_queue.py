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
from touchdown.tests.stubs.aws import QueueStubber


class TestQueueCreation(StubberTestCase):

    def test_create_queue(self):
        goal = self.create_goal('apply')

        queue = self.fixtures.enter_context(QueueStubber(
            goal.get_service(
                self.aws.add_queue(
                    name='test-queue',
                ),
                'apply',
            )
        ))

        queue.add_get_queue_url_404()
        queue.add_create_queue()

        queue.add_get_queue_url()
        queue.add_get_queue_attributes()

        queue.add_get_queue_url()
        queue.add_get_queue_attributes()

        goal.execute()

    def test_create_queue_idempotent(self):
        goal = self.create_goal('apply')

        queue = self.fixtures.enter_context(QueueStubber(
            goal.get_service(
                self.aws.add_queue(
                    name='test-queue',
                ),
                'apply',
            )
        ))

        queue.add_get_queue_url()
        queue.add_get_queue_attributes()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(queue.resource)), 0)


class TestQueueDestroy(StubberTestCase):

    def test_destroy_queue(self):
        goal = self.create_goal('destroy')

        queue = self.fixtures.enter_context(QueueStubber(
            goal.get_service(
                self.aws.add_queue(
                    name='test-queue',
                ),
                'destroy',
            )
        ))

        queue.add_get_queue_url()
        queue.add_get_queue_attributes()
        queue.add_delete_queue()

        goal.execute()

    def test_destroy_queue_idempotent(self):
        goal = self.create_goal('destroy')

        queue = self.fixtures.enter_context(QueueStubber(
            goal.get_service(
                self.aws.add_queue(
                    name='test-queue',
                ),
                'destroy',
            )
        ))

        queue.add_get_queue_url_404()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(queue.resource)), 0)
