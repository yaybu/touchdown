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

from touchdown.core import errors, goals, workspace
from touchdown.core.map import SerialMap
from touchdown.frontends import ConsoleFrontend


class TestTemplate(unittest.TestCase):

    def setUp(self):
        self.workspace = workspace.Workspace()

    def apply(self):
        self.apply_runner = goals.create(
            "apply",
            self.workspace,
            ConsoleFrontend(interactive=False),
            map=SerialMap
        )
        self.apply_runner.execute()
        return self.apply_runner

    def test_static_template(self):
        template = self.workspace.add_jinja2_template(
            name="foo",
            source="HELLO {{ name }}!",
            context={
                "name": "John",
            },
        )
        state = self.apply()
        self.assertEqual(
            state.get_service(template, "apply").object["Rendered"],
            "HELLO John!",
        )
