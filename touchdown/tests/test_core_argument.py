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

import netaddr

from touchdown.core import argument, errors


class TestArguments(unittest.TestCase):

    def test_bool_true(self):
        self.assertEqual(argument.Boolean().clean(None, 'on'), True)
        self.assertEqual(argument.Boolean().clean(None, 'yes'), True)
        self.assertEqual(argument.Boolean().clean(None, '1'), True)
        self.assertEqual(argument.Boolean().clean(None, 'true'), True)

    def test_bool_false(self):
        self.assertEqual(argument.Boolean().clean(None, 'off'), False)
        self.assertEqual(argument.Boolean().clean(None, 'no'), False)
        self.assertEqual(argument.Boolean().clean(None, '0'), False)
        self.assertEqual(argument.Boolean().clean(None, 'false'), False)

    def test_string(self):
        self.assertEqual(argument.String().clean(None, '0'), '0')

    def test_string_none(self):
        self.assertEqual(argument.String().clean(None, None), None)

    def test_integer_from_string(self):
        self.assertEqual(argument.Integer().clean(None, '0'), 0)

    def test_integer(self):
        self.assertEqual(argument.Integer().clean(None, 0), 0)

    def test_not_an_integer(self):
        self.assertRaises(
            errors.InvalidParameter,
            argument.Integer().clean,
            None,
            'five'
        )

    def test_ip_address(self):
        self.assertEqual(
            str(argument.IPAddress().clean(None, '192.168.0.1')),
            '192.168.0.1',
        )

    def test_ip_address_exception(self):
        self.assertRaises(
            errors.InvalidParameter,
            argument.IPAddress().clean,
            None,
            '192.168.0.1/24',
        )

    def test_ip_network(self):
        self.assertEqual(
            str(argument.IPNetwork().clean(None, '192.168.0.0/25')),
            '192.168.0.0/25',
        )

    def test_ip_network_exception(self):
        self.assertRaises(
            errors.InvalidParameter,
            argument.IPNetwork().clean,
            None,
            '192.168.0.270',
        )

    def test_dict(self):
        self.assertEqual(argument.Dict().clean(None, {}), {})

    def test_not_a_dict(self):
        self.assertRaises(
            errors.InvalidParameter,
            argument.Dict().clean,
            None,
            []
        )

    def test_list_ips(self):
        result = argument.List(argument.IPNetwork()).clean(None, ['0.0.0.0/0'])
        self.assertTrue(isinstance(result, list))
        self.assertTrue(isinstance(result[0], netaddr.IPNetwork))

    def test_list_invalid_ips(self):
        self.assertRaises(
            errors.InvalidParameter,
            argument.List(argument.IPNetwork()).clean,
            None,
            ['0.0.0.0/'],
        )

    def test_not_a_list(self):
        self.assertRaises(
            errors.InvalidParameter,
            argument.List().clean,
            None,
            {}
        )
