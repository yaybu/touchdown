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

import mock

from touchdown.tests.fixtures.folder import TemporaryFolderFixture
from touchdown.tests.testcases import WorkspaceTestCase


class TestFileAsString(WorkspaceTestCase):

    def test_echoing_file_as_string(self):
        goal = self.create_goal('apply')

        folder = self.fixtures.enter_context(TemporaryFolderFixture(goal, self.workspace))
        test_txt = folder.add_file(name='test.txt')
        self.workspace.add_echo(text=test_txt)

        goal.get_service(test_txt, 'set').execute('hello!!!')

        echo = self.fixtures.enter_context(mock.patch.object(goal.ui, 'echo'))
        goal.execute()

        echo.assert_called_with('[echo] hello!!!')
