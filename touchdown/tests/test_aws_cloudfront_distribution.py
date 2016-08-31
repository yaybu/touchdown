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

import unittest

import mock

from touchdown.aws.cloudfront.distribution import Describe
from touchdown.aws.session import session
from touchdown.tests.stubs.aws import DistributionStubber

from . import aws

CALLER_REFERENCE = 'e0324ac4-e30d-4cde-9b29-173863ac0861'

EXAMPLE_DISTRIBUTION_CONFIG = {
    'Aliases': {'Items': ['www.example.com'], 'Quantity': 1},
    'CacheBehaviors': {'Items': [], 'Quantity': 0},
    'CallerReference': CALLER_REFERENCE,
    'Comment': 'www.example.com',
    'CustomErrorResponses': {'Items': [], 'Quantity': 0},
    'DefaultCacheBehavior': {
        'AllowedMethods': {
            'CachedMethods': {'Items': ['GET', 'HEAD'], 'Quantity': 2},
            'Items': ['GET', 'HEAD'],
            'Quantity': 2,
        },
        'Compress': False,
        'DefaultTTL': 86400,
        'ForwardedValues': {
            'Cookies': {
                'Forward': 'none',
                'WhitelistedNames': {'Items': [], 'Quantity': 0},
            },
            'Headers': {'Items': [], 'Quantity': 0},
            'QueryString': True,
        },
        'MaxTTL': 31536000,
        'MinTTL': 0,
        'SmoothStreaming': False,
        'TargetOriginId': 'fred',
        'TrustedSigners': {'Enabled': False, 'Quantity': 0},
        'ViewerProtocolPolicy': 'allow-all'
    },
    'DefaultRootObject': '/',
    'Enabled': True,
    'Logging': {
        'Bucket': '',
        'Enabled': False,
        'IncludeCookies': False,
        'Prefix': ''
    },
    'Origins': {
        'Items': [{
            'CustomHeaders': {'Items': [], 'Quantity': 0},
            'CustomOriginConfig': {
                'HTTPPort': 80,
                'HTTPSPort': 443,
                'OriginProtocolPolicy': 'match-viewer',
                'OriginSslProtocols': {'Items': ['SSLv3', 'TLSv1'], 'Quantity': 2}
            },
            'DomainName': 'backend.example.com',
            'Id': 'fred',
            'OriginPath': ''
        }],
        'Quantity': 1,
    },
    'PriceClass': 'PriceClass_100',
    'Restrictions': {'GeoRestriction': {'Quantity': 0, 'RestrictionType': 'none'}},
    'ViewerCertificate': {
        'CertificateSource': 'cloudfront',
        'MinimumProtocolVersion': 'TLSv1',
        'SSLSupportMethod': 'sni-only'
    },
    'WebACLId': '',
}


class TestMetadata(unittest.TestCase):

    def test_waiter_waity_enough(self):
        waiter = session.get_waiter_model('cloudfront', api_version=Describe.api_version)
        self.assertEqual(waiter.get_waiter('DistributionDeployed').max_attempts, 50)


class TestDistributionCreation(aws.StubberTestCase):

    def test_create_distribution(self):
        goal = self.create_goal('apply')

        uuid4 = self.fixtures.enter_context(mock.patch('uuid.uuid4'))
        uuid4.return_value = CALLER_REFERENCE

        distribution = self.fixtures.enter_context(DistributionStubber(
            goal.get_service(
                self.aws.add_distribution(
                    name='www.example.com',
                    origins=[{
                        'name': 'fred',
                        'domain_name': 'backend.example.com',
                    }],
                    default_cache_behavior={
                        'target_origin': 'fred',
                    },
                ),
                'apply',
            )
        ))
        distribution.add_list_distributions_empty_response()

        distribution.add_create_distribution(EXAMPLE_DISTRIBUTION_CONFIG)

        distribution.add_list_distributions_one_response(EXAMPLE_DISTRIBUTION_CONFIG, status='InProgress')
        distribution.add_get_distribution(EXAMPLE_DISTRIBUTION_CONFIG, status='InProgress')
        distribution.add_get_distribution(EXAMPLE_DISTRIBUTION_CONFIG, status='Deployed')

        distribution.add_list_distributions_one_response(EXAMPLE_DISTRIBUTION_CONFIG, status='Deployed')
        distribution.add_get_distribution(EXAMPLE_DISTRIBUTION_CONFIG, status='Deployed')

        goal.execute()

    def test_create_distribution_idempotent(self):
        goal = self.create_goal('apply')

        uuid4 = self.fixtures.enter_context(mock.patch('uuid.uuid4'))
        uuid4.return_value = CALLER_REFERENCE

        distribution = self.fixtures.enter_context(DistributionStubber(
            goal.get_service(
                self.aws.add_distribution(
                    name='www.example.com',
                    origins=[{
                        'name': 'fred',
                        'domain_name': 'backend.example.com',
                    }],
                    default_cache_behavior={
                        'target_origin': 'fred',
                    },
                ),
                'apply',
            )
        ))

        distribution.add_list_distributions_one_response(EXAMPLE_DISTRIBUTION_CONFIG, status='Deployed')
        distribution.add_get_distribution(EXAMPLE_DISTRIBUTION_CONFIG, status='Deployed')

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(distribution.resource)), 0)


class TestDistributionDeletion(aws.StubberTestCase):

    def test_delete_distribution(self):
        goal = self.create_goal('destroy')

        uuid4 = self.fixtures.enter_context(mock.patch('uuid.uuid4'))
        uuid4.return_value = CALLER_REFERENCE

        distribution = self.fixtures.enter_context(DistributionStubber(
            goal.get_service(
                self.aws.add_distribution(
                    name='www.example.com',
                    origins=[{
                        'name': 'fred',
                        'domain_name': 'backend.example.com',
                    }],
                    default_cache_behavior={
                        'target_origin': 'fred',
                    },
                ),
                'destroy',
            )
        ))

        # Find the existing distribution
        distribution.add_list_distributions_one_response(EXAMPLE_DISTRIBUTION_CONFIG, status='Deployed')
        distribution.add_get_distribution(EXAMPLE_DISTRIBUTION_CONFIG, status='Deployed')

        # You have to disable the distribution before you can delete it
        distribution.add_update_distribution(distribution.disable(EXAMPLE_DISTRIBUTION_CONFIG))

        # Wait for the change to be replicated to all edges
        distribution.add_get_distribution(EXAMPLE_DISTRIBUTION_CONFIG, status='InProgress')
        distribution.add_get_distribution(EXAMPLE_DISTRIBUTION_CONFIG, status='InProgress')
        distribution.add_get_distribution(EXAMPLE_DISTRIBUTION_CONFIG, status='Deployed')

        # Refresh metadata after a wait
        distribution.add_list_distributions_one_response(EXAMPLE_DISTRIBUTION_CONFIG, status='Deployed')
        distribution.add_get_distribution(EXAMPLE_DISTRIBUTION_CONFIG, status='Deployed')

        # Actually delete it
        distribution.add_delete_distribution()

        goal.execute()

    def test_delete_distribution_idempotent(self):
        goal = self.create_goal('destroy')

        distribution = self.fixtures.enter_context(DistributionStubber(
            goal.get_service(
                self.aws.add_distribution(
                    name='www.example.com',
                    origins=[{
                        'name': 'fred',
                        'domain_name': 'backend.example.com',
                    }],
                    default_cache_behavior={
                        'target_origin': 'fred',
                    },
                ),
                'destroy',
            )
        ))

        distribution.add_list_distributions_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(distribution.resource)), 0)
