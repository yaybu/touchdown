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

from touchdown.aws.vpc import SecurityGroup
from touchdown.core import serializers


class TestSerializing(unittest.TestCase):

    def setUp(self):
        self.resource = SecurityGroup(None, name="test")
        self.runner = mock.Mock()

    def test_const(self):
        serializer = serializers.Const("FOO")
        self.assertEqual(serializer.render(self.runner, None), "FOO")

    def test_attribute(self):
        serializer = serializers.Argument("name")
        result = serializer.render(self.runner, self.resource)
        self.assertEqual(result, "test")

    def test_expression(self):
        serializer = serializers.Expression(lambda runner, object: object.name)
        result = serializer.render(self.runner, self.resource)
        self.assertEqual(result, "test")

    def test_required(self):
        serializer = serializers.Required(serializers.Argument("description"))
        self.assertRaises(serializers.RequiredFieldNotPresent, serializer.render, self.runner, self.resource)

    def test_boolean(self):
        serializer = serializers.Boolean(serializers.Const(1))
        result = serializer.render(self.runner, self.resource)
        self.assertEqual(result, True)

    def test_string(self):
        serializer = serializers.String(serializers.Const(1))
        result = serializer.render(self.runner, self.resource)
        self.assertEqual(result, "1")

    def test_integer(self):
        serializer = serializers.Integer(serializers.Const("1"))
        result = serializer.render(self.runner, self.resource)
        self.assertEqual(result, 1)

    def test_dict(self):
        serializer = serializers.Dict(Name=serializers.Argument("name"))
        result = serializer.render(self.runner, self.resource)
        self.assertEqual(result, {"Name": "test"})

    def test_list(self):
        serializer = serializers.List(serializers.Dict(Name=serializers.Argument("name")))
        result = serializer.render(self.runner, [self.resource])
        self.assertEqual(result, [{"Name": "test"}, ])
