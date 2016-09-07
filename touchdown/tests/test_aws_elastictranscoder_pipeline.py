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

from .aws import StubberTestCase
from .fixtures.aws import BucketFixture, RoleFixture
from .stubs.aws import PipelineStubber


class TestPipelineCreation(StubberTestCase):

    def test_create_pipeline(self):
        goal = self.create_goal('apply')

        bucket = self.fixtures.enter_context(BucketFixture(goal, self.aws))
        role = self.fixtures.enter_context(RoleFixture(goal, self.aws))

        pipeline = self.fixtures.enter_context(PipelineStubber(
            goal.get_service(
                self.aws.add_pipeline(
                    name='test-pipeline',
                    input_bucket=bucket.bucket,
                    role=role,
                ),
                'apply',
            )
        ))
        pipeline.add_list_pipelines_empty_response()
        pipeline.add_create_pipeline(
            input_bucket='my-test-bucket',
            role='12345678901234567890',
        )

        goal.execute()

    def test_create_pipeline_idempotent(self):
        goal = self.create_goal('apply')

        bucket = self.fixtures.enter_context(BucketFixture(goal, self.aws))
        role = self.fixtures.enter_context(RoleFixture(goal, self.aws))

        pipeline = self.fixtures.enter_context(PipelineStubber(
            goal.get_service(
                self.aws.add_pipeline(
                    name='test-pipeline',
                    input_bucket=bucket.bucket,
                    role=role,
                ),
                'apply',
            )
        ))
        pipeline.add_list_pipelines_one_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(pipeline.resource)), 0)


class TestPipelineDestroy(StubberTestCase):

    def test_destroy_pipeline(self):
        goal = self.create_goal('destroy')

        pipeline = self.fixtures.enter_context(PipelineStubber(
            goal.get_service(
                self.aws.add_pipeline(
                    name='test-pipeline',
                ),
                'destroy',
            )
        ))
        pipeline.add_list_pipelines_one_response()
        pipeline.add_delete_pipeline()

        goal.execute()

    def test_destroy_pipeline_idempotent(self):
        goal = self.create_goal('destroy')

        pipeline = self.fixtures.enter_context(PipelineStubber(
            goal.get_service(
                self.aws.add_pipeline(
                    name='test-pipeline',
                ),
                'destroy',
            )
        ))
        pipeline.add_list_pipelines_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(pipeline.resource)), 0)
