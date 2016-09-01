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

import os

from touchdown.tests.aws import StubberTestCase
from touchdown.tests.fixtures.folder import TemporaryFolderFixture
from touchdown.tests.stubs.aws import KeyStubber


DUMMY_EDITOR = (
    '#! /usr/bin/python\n'
    'import sys\n'
    'import time\n'
    'time.sleep(1)\n'
    'with open(sys.argv[1], "w") as fp:\n'
    '    fp.write("{message}")\n'
)


class TestKmsWrapper(StubberTestCase):

    def test_edit_file_encrypted_with_kms(self):
        goal = self.create_goal('edit')

        folder = self.fixtures.enter_context(TemporaryFolderFixture(goal, self.workspace))

        editor_path = os.path.join(folder.name, 'editor')
        with open(editor_path, 'w') as fp:
            fp.write(DUMMY_EDITOR.format(message='HEELOO'))
        os.chmod(editor_path, 0o755)

        key = self.fixtures.enter_context(KeyStubber(
            goal.get_service(
                self.aws.add_key(
                    name='test-key',
                ),
                'describe',
            )
        ))
        key.add_list_keys_one()
        key.add_describe_key()
        key.add_generate_data_key()
        key.add_decrypt()

        wrapped_file = key.resource.add_cipher(name='test.txt', file=folder.add_file(name='test.txt.kms'))

        os.environ['EDITOR'] = editor_path
        goal.execute('test.txt')

        reader = goal.get_service(wrapped_file, 'fileio')
        self.assertEqual(reader.read().read(), b'HEELOO')

    def test_inifile_string_encrypted_with_kms(self):
        goal = self.create_goal('set')

        folder = self.fixtures.enter_context(TemporaryFolderFixture(goal, self.workspace))

        key = self.fixtures.enter_context(KeyStubber(
            goal.get_service(
                self.aws.add_key(
                    name='test-key',
                ),
                'describe',
            )
        ))
        key.add_list_keys_one()
        key.add_describe_key()
        key.add_generate_data_key()
        key.add_decrypt()

        wrapped_file = key.resource.add_cipher(file=folder.add_file(name='test.cfg'))
        config_file = wrapped_file.add_ini_file()

        variable = config_file.add_string(
            name='strings.variable1',
            default='value1',
        )

        goal.execute('strings.variable1', '1eulav')

        getter = goal.get_service(variable, 'get')
        self.assertEqual(getter.execute(), ('1eulav', True))
