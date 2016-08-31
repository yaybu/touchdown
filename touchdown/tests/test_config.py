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

import itertools
import shutil
import tempfile
import unittest

from touchdown.core import errors, goals, serializers, workspace
from touchdown.core.map import SerialMap
from touchdown.frontends import ConsoleFrontend


class _Mixins(object):

    def setUp(self):
        self.counter = iter(itertools.count())

        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)

        self.workspace = workspace.Workspace()
        file = self.setup_file()
        self.setup_config(file)

    def setup_config(self, file):
        self.config = file.add_ini_file(
            file=file,
        )
        self.strings_variable1 = self.config.add_string(
            name='strings.variable1',
            default='value1',
        )
        self.integer_variable11 = self.config.add_integer(
            name='integers.variable1',
            default=1,
        )
        self.list_variable1 = self.config.add_list(
            name='lists.variable1',
            default=['foo', 'bar', 'baz'],
        )

    def get_goal(self, goal):
        return goals.create(
            goal,
            self.workspace,
            ConsoleFrontend(interactive=False),
            map=SerialMap
        )

    def call(self, command, *args, **kwargs):
        return self.get_goal(command).execute(*args, **kwargs)

    def get(self, name):
        return self.get_goal('get').collect_as_dict('get')[name].execute()

    def test_apply(self):
        self.assertRaises(
            errors.NothingChanged,
            self.call, 'apply'
        )

    def test_destroy(self):
        self.assertRaises(
            errors.NothingChanged,
            self.call, 'destroy'
        )

    def test_get_string(self):
        self.call('get', 'strings.variable1')
        self.assertEqual(self.get('strings.variable1'), ('value1', False))

    def test_set_string(self):
        self.call('set', 'strings.variable1', 'value2')
        self.call('get', 'strings.variable1')
        self.assertEqual(self.get('strings.variable1'), ('value2', True))

    def test_get_integer(self):
        self.call('get', 'integers.variable1')
        self.assertEqual(self.get('integers.variable1'), (1, False))

    def test_set_integer(self):
        self.call('set', 'integers.variable1', 2)
        self.call('get', 'integers.variable1')
        self.assertEqual(self.get('integers.variable1'), (2, True))

    def test_get_list(self):
        self.call('get', 'lists.variable1')
        self.assertEqual(self.get('lists.variable1'), (['foo', 'bar', 'baz'], False))

    def test_set_list(self):
        self.call('set', 'lists.variable1', 'foo,bar')
        self.call('get', 'lists.variable1')
        self.assertEqual(self.get('lists.variable1'), (['foo', 'bar'], True))

    def test_retain_list(self):
        self.config.add_list(
            name='lists.variable2',
            default=serializers.Expression(lambda ctx, value: [str(next(self.counter))]),
            retain_default=True,
        )
        assert self.get('lists.variable2') != self.get('lists.variable2')
        self.call('apply')
        self.assertRaises(errors.NothingChanged, self.call, 'apply')
        assert self.get('lists.variable2') == self.get('lists.variable2')

    def test_retain_ips(self):
        net = self.config.add_ip_allocations(
            name='subnets',
            network='10.30.0.0/20',
        )
        net.add_ip_allocation(
            name='app-a',
            size=25,
        )
        net.add_ip_allocation(
            name='app-b',
            size=25,
        )
        self.call('apply')
        self.assertRaises(errors.NothingChanged, self.call, 'apply')
        assert self.get('subnets.app-a') == '10.30.0.0/25'
        assert self.get('subnets.app-b') == '10.30.0.128/25'

    def test_echo_string(self):
        self.workspace.add_echo(
            text=self.strings_variable1,
        )
        self.call('apply')


class LocalFileTestCase(_Mixins, unittest.TestCase):

    def setup_file(self):
        folder = self.workspace.add_local_folder(name=self.test_dir)
        return folder.add_file(name='test.cfg')


class LocalFileWithGpgTestCase(_Mixins, unittest.TestCase):

    def setup_file(self):
        folder = self.workspace.add_local_folder(name=self.test_dir)
        gpg = self.workspace.add_gpg(passphrase='password', symmetric=True)
        return gpg.add_cipher(file=folder.add_file(name='test.cfg'))


class TestIpNetwork(_Mixins, unittest.TestCase):

    def setup_file(self):
        folder = self.workspace.add_local_folder(name=self.test_dir)
        return folder.add_file(name='test.cfg')

    def test_ensure_allocator_state_preserved(self):
        network = self.config.add_ip_network(name='environment.network')
        net = self.config.add_ip_allocations(
            name='subnets',
            network=network,
        )
        net.add_ip_allocation(
            name='app-a',
            size=25,
        )
        net.add_ip_allocation(
            name='app-b',
            size=25,
        )
        self.call('set', 'environment.network', '10.30.0.0/20')
        self.call('set', 'subnets.app-a', '10.30.0.0/25')
        self.call('apply')
        self.assertRaises(errors.NothingChanged, self.call, 'apply')
        assert self.get('subnets.app-a') == '10.30.0.0/25'
        assert self.get('subnets.app-b') == '10.30.0.128/25'
