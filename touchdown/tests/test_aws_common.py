# Copyright 2014 Isotoma Limited
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

from touchdown.core import serializers

from touchdown.aws.common import GenericAction
from touchdown.aws.elasticache import CacheCluster


class TestGenericAction(unittest.TestCase):

    def test_basic_call(self):
        api = mock.Mock()
        plan = mock.Mock()

        plan.resource = CacheCluster(None, name='freddy')

        g = GenericAction(plan, "I am an action", api, serializer=serializers.Resource())
        self.assertEqual(tuple(g.description), ("I am an action", ))
        g.run()

        api.assert_called_with(
            CacheClusterId='freddy',
        )
