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

import botocore.session
import mock
from botocore import xform_name

from touchdown.aws import common
from touchdown.aws.elasticache import CacheCluster
from touchdown.core import serializers


class TestGenericAction(unittest.TestCase):

    def test_basic_call(self):
        api = mock.Mock()
        plan = mock.Mock()

        plan.resource = CacheCluster(None, name='freddy')

        g = common.GenericAction(plan, "I am an action", api, serializer=serializers.Resource())
        self.assertEqual(tuple(g.description), ("I am an action", ))
        g.run()

        api.assert_called_with(
            NumCacheNodes=1,
            CacheClusterId='freddy',
        )


class TestSimpleDescribeImplementations(unittest.TestCase):

    ignore = (
        common.SimpleApply,
        common.SimpleDestroy,
    )

    def test_valid(self):
        session = botocore.session.get_session()
        for impl in common.SimpleDescribe.__subclasses__():
            if issubclass(impl, self.ignore):
                continue

            if getattr(impl, "describe_action", None) is None:
                continue

            service = session.get_service_model(impl.service_name)
            methods = {xform_name(s): s for s in service.operation_names}
            operation = service.operation_model(methods[impl.describe_action])

            if impl.describe_envelope == "@":
                continue

            if "." not in impl.describe_envelope and ":" not in impl.describe_envelope:
                assert impl.describe_envelope in operation.output_shape.members
