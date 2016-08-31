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
from touchdown.core import dependencies


class TestDependencies(unittest.TestCase):

    def test_consistent_order_forward(self):
        a = SecurityGroup(None, name='test', description='test')
        b = SecurityGroup(None, name='test', description='test')
        b.add_dependency(a)
        c = SecurityGroup(None, name='test', description='test')
        c.add_dependency(b)
        d = SecurityGroup(None, name='test', description='test')
        d.add_dependency(c)

        dw = dependencies.DependencyMap(d)
        self.assertEqual(list(dw.all()), [a, b, c, d])

    def test_consistent_order_backward(self):
        a = SecurityGroup(None, name='test', description='test')
        b = SecurityGroup(None, name='test', description='test')
        b.add_dependency(a)
        c = SecurityGroup(None, name='test', description='test')
        c.add_dependency(b)
        d = SecurityGroup(None, name='test', description='test')
        d.add_dependency(c)

        dw = dependencies.DependencyMap(d, tips_first=True)
        self.assertEqual(list(dw.all()), [d, c, b, a])
