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

from touchdown.tests.fixtures.ssh_connection import SshConnectionFixture
from touchdown.tests.testcases import WorkspaceTestCase


class TestSshClient(WorkspaceTestCase):

    @unittest.skip('test doesn\'t work on CI')
    def test_ssh_client(self):
        goal = self.create_goal('ssh')
        ssh_connection = self.fixtures.enter_context(SshConnectionFixture(goal, self.workspace))
        connection_plan = goal.get_service(ssh_connection.ssh_connection, 'describe')

        self.fixtures.enter_context(mock.patch('touchdown.ssh.client.Client.verify_transport'))
        self.fixtures.enter_context(mock.patch('touchdown.ssh.client.Client.set_input_encoding'))

        connection_plan.get_client()

        # FIXME: How to make the dummy server run stuff? Or fake run stuff.
