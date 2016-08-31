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

from touchdown.aws.vpc import SecurityGroup
from touchdown.core import serializers


class TestResource(unittest.TestCase):

    def setUp(self):
        self.resource = SecurityGroup(None, name='test')

    def test_identifier(self):
        self.assertTrue(isinstance(
            self.resource.identifier(),
            serializers.Context,
        ))

    def test_properties(self):
        self.assertTrue(isinstance(
            self.resource.get_property('Foo'),
            serializers.Property,
        ))
