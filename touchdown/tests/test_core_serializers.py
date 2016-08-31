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
        self.resource = SecurityGroup(None, name='test')
        self.runner = mock.Mock()

    def test_const(self):
        serializer = serializers.Const('FOO')
        self.assertEqual(serializer.render(self.runner, None), 'FOO')

    def test_attribute(self):
        serializer = serializers.Argument('name')
        result = serializer.render(self.runner, self.resource)
        self.assertEqual(result, 'test')

    def test_expression(self):
        serializer = serializers.Expression(lambda runner, object: object.name)
        result = serializer.render(self.runner, self.resource)
        self.assertEqual(result, 'test')

    def test_required(self):
        field = mock.Mock()
        field.argument.empty_serializer = None
        serializer = serializers.Required(serializers.Argument('description', field))
        self.assertRaises(serializers.RequiredFieldNotPresent, serializer.render, self.runner, self.resource)

    def test_boolean(self):
        serializer = serializers.Boolean(serializers.Const(1))
        result = serializer.render(self.runner, self.resource)
        self.assertEqual(result, True)

    def test_string(self):
        serializer = serializers.String(serializers.Const(1))
        result = serializer.render(self.runner, self.resource)
        self.assertEqual(result, '1')

    def test_integer(self):
        serializer = serializers.Integer(serializers.Const('1'))
        result = serializer.render(self.runner, self.resource)
        self.assertEqual(result, 1)

    def test_dict(self):
        serializer = serializers.Dict(Name=serializers.Argument('name'))
        result = serializer.render(self.runner, self.resource)
        self.assertEqual(result, {'Name': 'test'})

    def test_list(self):
        serializer = serializers.List(serializers.Dict(Name=serializers.Argument('name')))
        result = serializer.render(self.runner, [self.resource])
        self.assertEqual(result, [{'Name': 'test'}, ])


class TestDiffing(unittest.TestCase):

    def setUp(self):
        self.resource = SecurityGroup(None, name='test')
        self.runner = mock.Mock()

    def test_matches_false(self):
        d = serializers.Resource().diff(self.runner, self.resource, {})
        assert d.matches() is False

    def test_diffs(self):
        d = serializers.Resource().diff(self.runner, self.resource, {})
        assert list(d.lines()) == ['name: ', '    (unset) => \'test\'']

    def test_matches_true(self):
        d = serializers.Resource().diff(self.runner, self.resource, {
            'GroupName': 'test',
        })
        assert d.matches() is True

    def test_diffs_desc_set(self):
        self.resource.description = 'description'
        d = serializers.Resource().diff(self.runner, self.resource, {
            'GroupName': 'test',
            'Description': '',
        })
        assert d.matches() is False
        assert list(d.lines()) == ['description: ', '    \'\' => \'description\'']

    def test_diffs_desc_unset(self):
        self.resource.description = ''
        d = serializers.Resource().diff(self.runner, self.resource, {
            'GroupName': 'test',
            'Description': 'description',
        })
        assert list(d.lines()) == ['description: ', '    \'description\' => \'\'']
        assert d.matches() is False


class TestListOfStringsDiff(unittest.TestCase):

    def setUp(self):
        self.serializer = serializers.List(
            serializers.String(),
        )

    def diff(self, a, b):
        return self.serializer.diff(None, a, b)

    def test_match_1(self):
        self.assertEqual(True, self.diff([], []).matches())

    def test_match_2(self):
        self.assertEqual(True, self.diff(['a', 'b'], ['a', 'b']).matches())

    def test_all_inserts(self):
        d = self.diff(['a', 'b', 'c'], [])
        self.assertEqual(False, d.matches())
        self.assertEqual(len(d), 3)

        self.assertEqual(d.diffs[0][1].remote_value, '(unset)')
        self.assertEqual(d.diffs[0][1].local_value, '\'a\'')
        self.assertEqual(d.diffs[1][1].remote_value, '(unset)')
        self.assertEqual(d.diffs[1][1].local_value, '\'b\'')
        self.assertEqual(d.diffs[2][1].remote_value, '(unset)')
        self.assertEqual(d.diffs[2][1].local_value, '\'c\'')

    def test_all_deletes(self):
        d = self.diff([], ['a', 'b', 'c'])
        self.assertEqual(False, d.matches())
        self.assertEqual(len(d), 3)

        self.assertEqual(d.diffs[0][1].local_value, '(unset)')
        self.assertEqual(d.diffs[0][1].remote_value, '\'a\'')
        self.assertEqual(d.diffs[1][1].local_value, '(unset)')
        self.assertEqual(d.diffs[1][1].remote_value, '\'b\'')
        self.assertEqual(d.diffs[2][1].local_value, '(unset)')
        self.assertEqual(d.diffs[2][1].remote_value, '\'c\'')

    def test_delete_at_start(self):
        d = self.diff(['b', 'c'], ['a', 'b', 'c'])
        self.assertEqual(False, d.matches())
        self.assertEqual(len(d), 1)

        self.assertEqual(d.diffs[0][1].remote_value, '\'a\'')
        self.assertEqual(d.diffs[0][1].local_value, '(unset)')

    def test_delete_in_middle(self):
        d = self.diff(['a', 'c'], ['a', 'b', 'c'])
        self.assertEqual(False, d.matches())
        self.assertEqual(len(d), 1)

        self.assertEqual(d.diffs[0][1].remote_value, '\'b\'')
        self.assertEqual(d.diffs[0][1].local_value, '(unset)')

    def test_delete_at_end(self):
        d = self.diff(['a', 'b'], ['a', 'b', 'c'])
        self.assertEqual(False, d.matches())
        self.assertEqual(len(d), 1)

        self.assertEqual(d.diffs[0][1].remote_value, '\'c\'')
        self.assertEqual(d.diffs[0][1].local_value, '(unset)')

    def test_replace_at_start(self):
        d = self.diff(['Z', 'b', 'c'], ['a', 'b', 'c'])
        self.assertEqual(False, d.matches())
        self.assertEqual(len(d), 1)

        self.assertEqual(d.diffs[0][1].remote_value, '\'a\'')
        self.assertEqual(d.diffs[0][1].local_value, '\'Z\'')

    def test_replace_in_middle(self):
        d = self.diff(['a', 'Z', 'c'], ['a', 'b', 'c'])
        self.assertEqual(False, d.matches())
        self.assertEqual(len(d), 1)

        self.assertEqual(d.diffs[0][1].remote_value, '\'b\'')
        self.assertEqual(d.diffs[0][1].local_value, '\'Z\'')

    def test_replace_at_end(self):
        d = self.diff(['a', 'b', 'Z'], ['a', 'b', 'c'])
        self.assertEqual(False, d.matches())
        self.assertEqual(len(d), 1)

        self.assertEqual(d.diffs[0][1].remote_value, '\'c\'')
        self.assertEqual(d.diffs[0][1].local_value, '\'Z\'')

    def test_insert_at_start(self):
        d = self.diff(['Z', 'a', 'b', 'c'], ['a', 'b', 'c'])
        self.assertEqual(False, d.matches())
        self.assertEqual(len(d), 1)

        self.assertEqual(d.diffs[0][1].remote_value, '(unset)')
        self.assertEqual(d.diffs[0][1].local_value, '\'Z\'')

    def test_insert_in_middle(self):
        d = self.diff(['a', 'Z', 'b', 'c'], ['a', 'b', 'c'])
        self.assertEqual(False, d.matches())
        self.assertEqual(len(d), 1)

        self.assertEqual(d.diffs[0][1].remote_value, '(unset)')
        self.assertEqual(d.diffs[0][1].local_value, '\'Z\'')

    def test_insert_at_end(self):
        d = self.diff(['a', 'b', 'c', 'Z'], ['a', 'b', 'c'])
        self.assertEqual(False, d.matches())
        self.assertEqual(len(d), 1)

        self.assertEqual(d.diffs[0][1].remote_value, '(unset)')
        self.assertEqual(d.diffs[0][1].local_value, '\'Z\'')
