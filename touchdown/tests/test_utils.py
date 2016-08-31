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

from touchdown.core.utils import force_bytes, force_str, force_unicode


class TestStringHelpers(unittest.TestCase):

    def test_str_str(self):
        self.assertEqual(force_str('foo'), 'foo')

    def test_str_u(self):
        self.assertEqual(force_str(u'foo'), 'foo')

    def test_str_b(self):
        self.assertEqual(force_str(b'foo'), 'foo')

    def test_str_exception(self):
        self.assertRaises(ValueError, force_str, [])

    def test_unicode_str(self):
        self.assertEqual(force_unicode('foo'), u'foo')

    def test_unicode_u(self):
        self.assertEqual(force_unicode(u'foo'), u'foo')

    def test_unicode_b(self):
        self.assertEqual(force_unicode(b'foo'), u'foo')

    def test_unicode_exception(self):
        self.assertRaises(ValueError, force_unicode, [])

    def test_bytes_str(self):
        self.assertEqual(force_bytes('foo'), b'foo')

    def test_bytes_u(self):
        self.assertEqual(force_bytes(u'foo'), b'foo')

    def test_bytes_b(self):
        self.assertEqual(force_bytes(b'foo'), b'foo')

    def test_bytes_exception(self):
        self.assertRaises(ValueError, force_bytes, [])
