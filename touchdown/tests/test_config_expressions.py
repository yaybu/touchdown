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

from touchdown.config import expressions
from touchdown.core import serializers


class TestExpressions(unittest.TestCase):

    def test_pwgen(self):
        serializer = expressions.pwgen(length=31, symbols=True)
        self.assertTrue(isinstance(serializer, serializers.Expression))
        rendered = serializer.render(None, None)
        self.assertEqual(len(rendered), 31)

    def test_django_key(self):
        serializer = expressions.django_secret_key()
        self.assertTrue(isinstance(serializer, serializers.Expression))
        rendered = serializer.render(None, None)
        self.assertEqual(len(rendered), 50)

    def test_fernet_key(self):
        serializer = expressions.fernet_secret_key()
        self.assertTrue(isinstance(serializer, serializers.Expression))
        rendered = serializer.render(None, None)
        self.assertEqual(len(rendered), 44)

    def test_rsa_private_key(self):
        serializer = expressions.rsa_private_key()
        self.assertTrue(isinstance(serializer, serializers.Expression))
        rendered = serializer.render(None, None).splitlines()
        self.assertEqual(
            rendered[0],
            '-----BEGIN RSA PRIVATE KEY-----',
        )
        self.assertEqual(
            rendered[-1],
            '-----END RSA PRIVATE KEY-----',
        )

    def test_dsa_private_key(self):
        serializer = expressions.rsa_private_key()
        self.assertTrue(isinstance(serializer, serializers.Expression))
        rendered = serializer.render(None, None).splitlines()
        self.assertEqual(
            rendered[0],
            '-----BEGIN RSA PRIVATE KEY-----',
        )
        self.assertEqual(
            rendered[-1],
            '-----END RSA PRIVATE KEY-----',
        )
