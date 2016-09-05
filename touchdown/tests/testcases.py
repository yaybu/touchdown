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

from touchdown.core import goals, workspace
from touchdown.core.map import SerialMap
from touchdown.frontends import ConsoleFrontend, MultiFrontend

try:
    from contextlib import ExitStack
except ImportError:
    from contextlib2 import ExitStack


class WorkspaceTestCase(unittest.TestCase):

    def setUp(self):
        self.workspace = workspace.Workspace()
        self.fixtures = ExitStack()
        self.addCleanup(self.fixtures.close)

    def create_goal(self, goal_name, map_class=SerialMap):
        return goals.create(
            goal_name,
            self.workspace,
            MultiFrontend([
                ConsoleFrontend(interactive=False),
            ]),
            map=map_class,
        )
