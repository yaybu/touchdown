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

from touchdown.aws.cloudfront import Distribution
from touchdown.aws.session import session
from touchdown.core import errors, serializers

from . import aws


class TestMetadata(unittest.TestCase):

    def test_waiter_waity_enough(self):
        waiter = session.get_waiter_model("cloudfront")
        self.assertEqual(waiter.get_waiter("DistributionDeployed").max_attempts, 50)


class TestCloudFrontDistributionSerializing(unittest.TestCase):

    def setUp(self):
        uuid = mock.Mock()
        uuid.return_value = "e64daba4-dddf-478e-a39b-b15a74325330"

        self.uuid = mock.patch('uuid.uuid4', uuid)
        self.uuid.start()

    def tearDown(self):
        self.uuid.stop()

    def test_simple_distribution(self):
        distribution = Distribution(
            None,
            name="example.com",
        )
        result = serializers.Resource().render(mock.Mock(), distribution)
        del result['CallerReference']
        self.assertEqual(result, {
            'Origins': {'Items': [], 'Quantity': 0},
            'Restrictions': {'GeoRestriction': {'RestrictionType': 'none', 'Quantity': 0}},
            'DefaultRootObject': '/',
            'PriceClass': 'PriceClass_100',
            'Enabled': True,
            'CustomErrorResponses': {'Items': [], 'Quantity': 0},
            'CacheBehaviors': {'Items': [], 'Quantity': 0},
            'Aliases': {'Items': ['example.com'], 'Quantity': 1},
            'Logging': {'Enabled': False, 'Prefix': '', 'Bucket': '', 'IncludeCookies': False},
            'Comment': 'example.com',
            'ViewerCertificate': {
                'CertificateSource': 'cloudfront',
                'MinimumProtocolVersion': 'TLSv1',
                'SSLSupportMethod': 'sni-only'
            },
            'WebACLId': '',
        })

    def test_simple_distribution_with_aliases(self):
        distribution = Distribution(
            None,
            name="example.com",
            aliases=['www.example.com'],
        )
        result = serializers.Resource().render(mock.Mock(), distribution)
        del result['CallerReference']
        self.assertEqual(result, {
            'Origins': {'Items': [], 'Quantity': 0},
            'Restrictions': {'GeoRestriction': {'RestrictionType': 'none', 'Quantity': 0}},
            'DefaultRootObject': '/',
            'PriceClass': 'PriceClass_100',
            'Enabled': True,
            'CustomErrorResponses': {'Items': [], 'Quantity': 0},
            'CacheBehaviors': {'Items': [], 'Quantity': 0},
            'Aliases': {'Items': ['example.com', 'www.example.com'], 'Quantity': 2},
            'Logging': {'Enabled': False, 'Prefix': '', 'Bucket': '', 'IncludeCookies': False},
            'Comment': 'example.com',
            'ViewerCertificate': {
                'CertificateSource': 'cloudfront',
                'MinimumProtocolVersion': 'TLSv1',
                'SSLSupportMethod': 'sni-only'
            },
            'WebACLId': '',
        })


class TestCloudFront(aws.TestBasicUsage):

    def setUpResource(self):
        self.expected_resource_id = 'EDFDVBD6EXAMPLE'
        self.resource = self.aws.add_distribution(
            name='www.example.com',
            origins=[{
                "name": "fred",
                "domain_name": "backend.example.com",
            }],
            default_cache_behavior={
                "target_origin": "fred",
            },
        )

    # FIXME: Refactor tests so matching can be done in a generic way
    def test_no_change(self):
        return
        self.responses.add_fixture("GET", "https://cloudfront.amazonaws.com/2016-01-28/distribution", self.fixture_found, expires=1)
        self.responses.add_fixture(
            "GET",
            "https://cloudfront.amazonaws.com/2016-01-28/distribution/EDFDVBD6EXAMPLE",
            "aws_distribution_get",
            expires=1
        )
        self.assertRaises(errors.NothingChanged, self.goal.execute)
        self.assertEqual(self.plan.resource_id, self.expected_resource_id)

    # FIXME: Refactor tests so matching can be done in a generic way
    def test_create(self):
        self.responses.add_fixture("GET", "https://cloudfront.amazonaws.com/2016-01-28/distribution", self.fixture_404, expires=1)
        self.responses.add_fixture("POST", self.base_url, self.fixture_create, expires=1)
        self.responses.add_fixture("GET", "https://cloudfront.amazonaws.com/2016-01-28/distribution", self.fixture_found)
        self.responses.add_fixture("GET", "https://cloudfront.amazonaws.com/2016-01-28/distribution/EDFDVBD6EXAMPLE", "aws_distribution_get")
        self.goal.execute()
        self.assertEqual(self.plan.resource_id, self.expected_resource_id)
