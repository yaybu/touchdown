# Copyright 2016 Isotoma Limited
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

import mock

from touchdown.core.map import ParallelMap
from touchdown.tests.testcases import WorkspaceTestCase


class TestParallelMap(WorkspaceTestCase):

    def test_parallel_map(self):
        # Use echo resources and set up the deps so that D depends on B and
        # C and B and C depend on A. Capture the order they run in and assert
        # that A ran first and D ran last.

        goal = self.create_goal('apply', map_class=ParallelMap)

        call_order = []
        echo = self.fixtures.enter_context(mock.patch.object(goal.ui, 'echo'))

        def append(text):
            if not text.startswith('[echo] '):
                return
            if text == '[echo] Echo to console':
                return
            call_order.append(text[-1])

        echo.side_effect = append

        a = self.workspace.add_echo(text='A')

        b = self.workspace.add_echo(text='B')
        b.add_dependency(a)

        c = self.workspace.add_echo(text='C')
        c.add_dependency(a)

        d = self.workspace.add_echo(text='D')
        d.add_dependency(b)
        d.add_dependency(c)

        goal.execute()

        assert call_order[0] == 'A'
        assert call_order[1] in 'BC'
        assert call_order[2] in 'BC'
        assert call_order[3] == 'D'
