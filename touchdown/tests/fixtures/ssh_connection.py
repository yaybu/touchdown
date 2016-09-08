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
import socket
import threading

import paramiko

from touchdown.tests.fixtures.fixture import Fixture


class DummyServer(paramiko.ServerInterface):

    def get_allowed_auths(self, username):
        return 'publickey,password'

    def check_auth_password(self, username, password):
        return paramiko.AUTH_SUCCESSFUL

    def check_auth_publickey(self, username, key):
        return paramiko.AUTH_SUCCESSFUL

    def check_channel_request(self, kind, chanid):
        return paramiko.OPEN_SUCCEEDED

    def check_channel_exec_request(self, channel, command):
        return True

    def check_channel_shell_request(self, channel):
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True


class SshConnectionFixture(Fixture):

    def __enter__(self):
        self.listen_socket = socket.socket()
        self.listen_socket.bind(('0.0.0.0', 0))
        self.listen_socket.listen(1)
        self.address, self.port = self.listen_socket.getsockname()
        self.fixtures.push(lambda *exc_info: self.listen_socket.close())
        self.event = threading.Event()

        self.ssh_connection = self.workspace.add_ssh_connection(
            name='test-ssh-connection',
            hostname=self.address,
            port=self.port,
        )

        self.listen_thread = threading.Thread(target=self.server_thread)
        self.listen_thread.daemon = True
        self.listen_thread.start()

        return self

    def server_thread(self):
        self.client_socket, addr = self.listen_socket.accept()
        self.fixtures.push(lambda *exc_info: self.client_socket.close())

        self.server_transport = paramiko.Transport(self.client_socket)
        self.fixtures.push(lambda *exc_info: self.server_transport.close())

        self.server_transport.add_server_key(
            paramiko.RSAKey.from_private_key_file(
                os.path.join(
                    os.path.dirname(__file__),
                    '..',
                    'assets/id_rsa_test',
                ),
            ),
        )

        self.server = DummyServer()
        self.server_transport.start_server(self.event, self.server)
