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

import os
import unittest
import six
import tempfile

from touchdown.core import workspace, errors
from touchdown.core.runner import Runner
from touchdown.core.main import ConsoleInterface
from touchdown.core.utils import force_bytes


class TestCase(unittest.TestCase):

    def setUp(self):
        self.workspace = workspace.Workspace()

    def apply(self):
        self.apply_runner = Runner("apply", self.workspace, ConsoleInterface(interactive=False))
        self.apply_runner.apply()

    def test_destroy(self):
        self.destroy_runner = Runner("destroy", self.workspace, ConsoleInterface(interactive=False))
        self.assertRaises(errors.NothingChanged, self.destroy_runner.apply)

    def test_file_apply(self):
        with tempfile.NamedTemporaryFile(delete=True) as fp:
            bundle = self.workspace.add_fuselage_bundle(
                target=self.workspace.add_local(),
            )
            bundle.add_file(
                name=fp.name,
                contents="hello",
            )
            self.apply()
            self.assertTrue(os.path.exists(fp.name))
            self.assertEquals(open(fp.name, "r").read(), "hello")

    def test_file_remove(self):
        with tempfile.NamedTemporaryFile(delete=False) as fp:
            fp.write("HELLO")

        bundle = self.workspace.add_fuselage_bundle(
            target=self.workspace.add_local(),
        )
        bundle.add_file(
            name=fp.name,
            policy="remove",
        )
        self.apply()
        self.assertFalse(os.path.exists(fp.name))
