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

from touchdown.core.errors import InvalidParameter
from touchdown.tests.aws import StubberTestCase
from touchdown.tests.stubs.aws import BucketStubber


class TestBucketDescribe(StubberTestCase):

    def test_annotate_object(self):
        goal = self.create_goal('apply')

        bucket = self.fixtures.enter_context(BucketStubber(
            goal.get_service(
                self.aws.add_bucket(name='mybucket'),
                'describe',
            )
        ))
        bucket.add_get_bucket_location()
        bucket.add_get_bucket_cors()
        bucket.add_get_bucket_policy()
        bucket.add_get_bucket_notification_configuration()
        bucket.add_get_bucket_accelerate_configuration()

        obj = bucket.service.annotate_object({
            'Name': 'ZzZzZz'
        })

        # Assert name isn't trodden on by annotate_object
        self.assertEqual(obj['Name'], 'ZzZzZz')


class TestBucketValidation(StubberTestCase):

    def test_starts_with_period(self):
        self.assertRaises(InvalidParameter, self.aws.add_bucket, name='.foo')

    def test_ends_with_period(self):
        self.assertRaises(InvalidParameter, self.aws.add_bucket, name='foo.')

    def test_double_period(self):
        self.assertRaises(InvalidParameter, self.aws.add_bucket, name='foo..bar')

    def test_starts_with_hyphen(self):
        self.assertRaises(InvalidParameter, self.aws.add_bucket, name='-foo')

    def test_ends_with_hyphen(self):
        self.assertRaises(InvalidParameter, self.aws.add_bucket, name='foo-')

    def test_hyphen(self):
        self.aws.add_bucket(name='foo--bar')

    def test_upper(self):
        self.assertRaises(InvalidParameter, self.aws.add_bucket, name='FOO')
