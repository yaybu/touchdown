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

import mock

from touchdown.tests.fixtures.aws import BucketFixture
from touchdown.tests.stubs.aws import StreamingDistributionStubber

from . import aws

CALLER_REFERENCE = 'e0324ac4-e30d-4cde-9b29-173863ac0861'

EXAMPLE_DISTRIBUTION_CONFIG = {
    'Aliases': {'Items': ['www.example.com'], 'Quantity': 1},
    'CallerReference': CALLER_REFERENCE,
    'Comment': 'www.example.com',
    'TrustedSigners': {'Enabled': False, 'Quantity': 0},
    'Enabled': True,
    'Logging': {
        'Enabled': False,
        'Bucket': '',
        'Prefix': '',
    },
    'S3Origin': {
        'DomainName': 'my-test-bucket.s3.amazonaws.com',
        'OriginAccessIdentity': '',
    },
    'PriceClass': 'PriceClass_100',
}


class TestStreamingDistributionCreation(aws.StubberTestCase):

    def test_create_streaming_distribution(self):
        goal = self.create_goal('apply')

        uuid4 = self.fixtures.enter_context(mock.patch('uuid.uuid4'))
        uuid4.return_value = CALLER_REFERENCE

        bucket = self.fixtures.enter_context(BucketFixture(goal, self.aws))

        streaming_distribution = self.fixtures.enter_context(StreamingDistributionStubber(
            goal.get_service(
                self.aws.add_streaming_distribution(
                    name='www.example.com',
                    bucket=bucket.bucket,
                ),
                'apply',
            )
        ))
        streaming_distribution.add_list_streaming_distributions_empty_response()

        streaming_distribution.add_create_streaming_distribution(EXAMPLE_DISTRIBUTION_CONFIG)

        streaming_distribution.add_list_streaming_distributions_one_response(EXAMPLE_DISTRIBUTION_CONFIG, status='InProgress')
        streaming_distribution.add_get_streaming_distribution(EXAMPLE_DISTRIBUTION_CONFIG, status='InProgress')
        streaming_distribution.add_get_streaming_distribution(EXAMPLE_DISTRIBUTION_CONFIG, status='Deployed')

        streaming_distribution.add_list_streaming_distributions_one_response(EXAMPLE_DISTRIBUTION_CONFIG, status='Deployed')
        streaming_distribution.add_get_streaming_distribution(EXAMPLE_DISTRIBUTION_CONFIG, status='Deployed')

        goal.execute()

    def test_create_streaming_distribution_idempotent(self):
        goal = self.create_goal('apply')

        uuid4 = self.fixtures.enter_context(mock.patch('uuid.uuid4'))
        uuid4.return_value = CALLER_REFERENCE

        bucket = self.fixtures.enter_context(BucketFixture(goal, self.aws))

        streaming_distribution = self.fixtures.enter_context(StreamingDistributionStubber(
            goal.get_service(
                self.aws.add_streaming_distribution(
                    name='www.example.com',
                    bucket=bucket.bucket,
                ),
                'apply',
            )
        ))

        streaming_distribution.add_list_streaming_distributions_one_response(EXAMPLE_DISTRIBUTION_CONFIG, status='Deployed')
        streaming_distribution.add_get_streaming_distribution(EXAMPLE_DISTRIBUTION_CONFIG, status='Deployed')

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(streaming_distribution.resource)), 0)


class TestStreamingDistributionDeletion(aws.StubberTestCase):

    def test_delete_streaming_distribution(self):
        goal = self.create_goal('destroy')

        uuid4 = self.fixtures.enter_context(mock.patch('uuid.uuid4'))
        uuid4.return_value = CALLER_REFERENCE

        bucket = self.fixtures.enter_context(BucketFixture(goal, self.aws))

        streaming_distribution = self.fixtures.enter_context(StreamingDistributionStubber(
            goal.get_service(
                self.aws.add_streaming_distribution(
                    name='www.example.com',
                    bucket=bucket.bucket,
                ),
                'destroy',
            )
        ))

        # Find the existing streaming_distribution
        streaming_distribution.add_list_streaming_distributions_one_response(EXAMPLE_DISTRIBUTION_CONFIG, status='Deployed')
        streaming_distribution.add_get_streaming_distribution(EXAMPLE_DISTRIBUTION_CONFIG, status='Deployed')

        # You have to disable the streaming_distribution before you can delete it
        streaming_distribution.add_update_streaming_distribution(streaming_distribution.disable(EXAMPLE_DISTRIBUTION_CONFIG))

        # Wait for the change to be replicated to all edges
        streaming_distribution.add_get_streaming_distribution(EXAMPLE_DISTRIBUTION_CONFIG, status='InProgress')
        streaming_distribution.add_get_streaming_distribution(EXAMPLE_DISTRIBUTION_CONFIG, status='InProgress')
        streaming_distribution.add_get_streaming_distribution(EXAMPLE_DISTRIBUTION_CONFIG, status='Deployed')

        # Refresh metadata after a wait
        streaming_distribution.add_list_streaming_distributions_one_response(EXAMPLE_DISTRIBUTION_CONFIG, status='Deployed')
        streaming_distribution.add_get_streaming_distribution(EXAMPLE_DISTRIBUTION_CONFIG, status='Deployed')

        # Actually delete it
        streaming_distribution.add_delete_streaming_distribution()

        goal.execute()

    def test_delete_streaming_distribution_idempotent(self):
        goal = self.create_goal('destroy')

        streaming_distribution = self.fixtures.enter_context(StreamingDistributionStubber(
            goal.get_service(
                self.aws.add_streaming_distribution(
                    name='www.example.com',
                ),
                'destroy',
            )
        ))

        streaming_distribution.add_list_streaming_distributions_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(streaming_distribution.resource)), 0)
