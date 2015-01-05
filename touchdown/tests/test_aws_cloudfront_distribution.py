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

from touchdown.aws import serializers
from touchdown.aws.cloudfront import Distribution


class TestCloudFrontDistributionSerializing(unittest.TestCase):

    def test_simple_distribution(self):
        distribution = Distribution(
            None,
            name="example.com",
        )
        result = serializers.Resource().render(mock.Mock(), distribution)
        self.assertEqual(result, {
            'Origins': {'Items': (), 'Quantity': 0},
            'Restrictions': {'GeoRestriction': {'RestrictionType': 'none'}},
            'DefaultRootObject': '/',
            'PriceClass': 'PriceClass_100',
            'Enabled': True,
            'CustomErrorResponses': {'Items': (), 'Quantity': 0},
            'CacheBehaviors': {'Items': (), 'Quantity': 0},
            'Aliases': {'Items': ('example.com',), 'Quantity': 1},
        })
