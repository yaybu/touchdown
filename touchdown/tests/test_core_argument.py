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

    def test_list_ips(self):
        result = argument.List(argument.IPNetwork()).clean(None, ["0.0.0.0/0"])
        self.assertTrue(isinstance(result, list))
        self.assertTrue(isinstance(result[0], netaddr.IPNetwork))

    def test_list_invalid_ips(self):
        self.assertRaises(
            errors.InvalidParameter,
            argument.List(argument.IPNetwork()).clean,
            None,
            ["0.0.0.0/"],
        )
