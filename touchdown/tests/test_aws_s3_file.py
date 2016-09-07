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
from touchdown.tests.fixtures.aws import BucketFixture
from touchdown.tests.stubs.aws import S3FileStubber


class TestBucketCreation(StubberTestCase):

    def test_create_bucket(self):
        goal = self.create_goal('apply')

        bucket = self.fixtures.enter_context(BucketFixture(goal, self.aws))

        s3_file = self.fixtures.enter_context(S3FileStubber(
            goal.get_service(
                bucket.bucket.add_file(
                    name='my-file',
                    contents='my-test-content',
                ),
                'apply',
            )
        ))
        s3_file.add_list_objects_empty_response()
        s3_file.add_put_object()
        s3_file.add_list_objects_one_response()
        s3_file.add_list_objects_one_response()
        s3_file.add_list_objects_one_response()

        goal.execute()

    def test_create_bucket_idempotent(self):
        goal = self.create_goal('apply')

        bucket = self.fixtures.enter_context(BucketFixture(goal, self.aws))

        s3_file = self.fixtures.enter_context(S3FileStubber(
            goal.get_service(
                bucket.bucket.add_file(
                    name='my-file',
                    contents='my-test-content',
                ),
                'apply',
            )
        ))
        s3_file.add_list_objects_one_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(s3_file.resource)), 0)


class TestBucketDeletion(StubberTestCase):

    def test_delete_bucket(self):
        goal = self.create_goal('destroy')

        bucket = self.fixtures.enter_context(BucketFixture(goal, self.aws))

        s3_file = self.fixtures.enter_context(S3FileStubber(
            goal.get_service(
                bucket.bucket.add_file(
                    name='my-file',
                ),
                'destroy',
            )
        ))
        s3_file.add_list_objects_one_response()
        s3_file.add_delete_object()

        goal.execute()

    def test_delete_bucket_idempotent(self):
        goal = self.create_goal('destroy')

        bucket = self.fixtures.enter_context(BucketFixture(goal, self.aws))

        s3_file = self.fixtures.enter_context(S3FileStubber(
            goal.get_service(
                bucket.bucket.add_file(
                    name='my-file',
                ),
                'destroy',
            )
        ))
        s3_file.add_list_objects_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(s3_file.resource)), 0)
