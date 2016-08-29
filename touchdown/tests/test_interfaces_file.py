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


class TestFile(WorkspaceTestCase):

    def test_get(self):
        # Test `touchdown get file.txt` works for any resource implementing the
        # file interface
        goal = self.create_goal('get')

        folder = self.fixtures.enter_context(TemporaryFolderFixture(goal, self.workspace))
        test_txt = folder.add_file(name='test.txt')

        goal.get_service(test_txt, 'set').execute('hello!!!')

        echo = self.fixtures.enter_context(mock.patch.object(goal.ui, 'echo'))
        goal.execute('test.txt')
        echo.assert_called_with('hello!!! (overriden by user)')

    def test_set(self):
        # Test `touchdown set file.txt value` works for any resource implementing the
        # file interface
        goal = self.create_goal('set')

        folder = self.fixtures.enter_context(TemporaryFolderFixture(goal, self.workspace))
        test_txt = folder.add_file(name='test.txt')

        goal.execute('test.txt', 'hello!!!')

        self.assertEqual(goal.get_service(test_txt, 'get').execute(), ('hello!!!', True))

    def test_echoing_file_as_string(self):
        # This ensures that a file resource can be used anywhere a string can
        # E.g. to echo the contents of the file ~/myfolder/myfile.txt:
        # fl = workspace.add_local_folder(name='~/myfolder')
        # fi = fl.add_file(name='myfile.txt')
        # workspace.add_echo(text=fi)

        goal = self.create_goal('apply')

        folder = self.fixtures.enter_context(TemporaryFolderFixture(goal, self.workspace))
        test_txt = folder.add_file(name='test.txt')
        self.workspace.add_echo(text=test_txt)

        goal.get_service(test_txt, 'set').execute('hello!!!')

        echo = self.fixtures.enter_context(mock.patch.object(goal.ui, 'echo'))
        goal.execute()

        echo.assert_called_with('[echo] hello!!!')
