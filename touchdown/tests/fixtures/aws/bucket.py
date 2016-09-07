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

from touchdown.tests.stubs.aws import BucketStubber

from .fixture import AwsFixture


class BucketFixture(AwsFixture):

    def __enter__(self):
        self.bucket_stubber = self.fixtures.enter_context(BucketStubber(
            self.goal.get_service(
                self.aws.get_bucket(
                    name='my-test-bucket',
                ),
                'describe',
            ),
        ))
        self.bucket_stubber.add_list_buckets_one_response()
        self.bucket_stubber.add_head_bucket()
        self.bucket_stubber.add_get_bucket_location()
        self.bucket_stubber.add_get_bucket_cors()
        self.bucket_stubber.add_get_bucket_policy()
        self.bucket_stubber.add_get_bucket_notification_configuration()
        self.bucket_stubber.add_get_bucket_accelerate_configuration()

        self.bucket = self.bucket_stubber.resource

        return self
