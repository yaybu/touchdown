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
import tempfile

from touchdown.core import errors, serializers
from touchdown.tests.testcases import WorkspaceTestCase


class TestCase(WorkspaceTestCase):

    def apply(self):
        goal = self.create_goal('apply')
        goal.execute()
        return goal

    def test_destroy(self):
        goal = self.create_goal('destroy')
        self.assertRaises(errors.NothingChanged, goal.execute)

    def test_file_apply(self):
        with tempfile.NamedTemporaryFile(delete=True) as fp:
            fp.close()

            bundle = self.workspace.add_fuselage_bundle(
                target=self.workspace.add_local(),
            )
            bundle.add_file(
                name=fp.name,
                contents='hello',
            )
            self.apply()
            self.assertTrue(os.path.exists(fp.name))
            self.assertEquals(open(fp.name, 'r').read(), 'hello')

    def test_file_apply_serializers(self):
        with tempfile.NamedTemporaryFile(delete=True) as fp:
            fp.close()

            bundle = self.workspace.add_fuselage_bundle(
                target=self.workspace.add_local(),
            )
            bundle.add_file(
                name=fp.name,
                contents=serializers.Const('hello'),
            )
            self.apply()
            self.assertEquals(open(fp.name, 'r').read(), 'hello')

    def test_file_remove(self):
        with tempfile.NamedTemporaryFile(delete=False) as fp:
            fp.write(b'HELLO')

        bundle = self.workspace.add_fuselage_bundle(
            target=self.workspace.add_local(),
        )
        bundle.add_file(
            name=fp.name,
            policy='remove',
        )
        self.apply()
        self.assertFalse(os.path.exists(fp.name))

    def test_output(self):
        with tempfile.NamedTemporaryFile(delete=True) as fp:
            fp.close()

            bundle = self.workspace.add_fuselage_bundle(
                target=self.workspace.add_local(),
            )
            bundle.add_file(
                name=fp.name,
                contents=serializers.Const('hello'),
            )

            output = bundle.add_output(name=fp.name)
            echo = self.workspace.add_echo(text=output)

            self.assertEqual(
                self.apply().get_service(echo, 'apply').object['Text'],
                'hello',
            )

    def test_no_changes(self):
        bundle = self.workspace.add_fuselage_bundle(
            target=self.workspace.add_local(),
        )
        bundle.add_file(
            name='ZZZZ__FILE_DOES_NOT_EXIST__ZZZZ',
            policy='remove',
        )
        apply_service = self.create_goal('apply')
        self.assertEqual(len(list(apply_service.plan())), 0)
