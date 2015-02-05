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

import binascii
import os
import socket
import time

import six
import paramiko

from touchdown.core import errors


def private_key_from_string(private_key):
    for cls in (paramiko.RSAKey, paramiko.ECDSAKey, paramiko.DSSKey):
        try:
            key = cls.from_private_key(six.BytesIO(private_key))
        except paramiko.SSHException:
            continue
        return key


class Client(paramiko.SSHClient):

    connection_attempts = 20

    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)
        self.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def _run(self, transport, command):
        channel = transport.open_session()
        try:
            channel.exec_command(command)

            # We don't want a stdin
            channel.makefile('wb', -1).close()

            # FIXME: It would be better to block with select
            exit_status_ready = channel.exit_status_ready()
            while not exit_status_ready:
                while channel.recv_ready():
                    print(channel.recv(1024))
                while channel.recv_stderr_ready():
                    print(channel.recv_stderr(1024))
                time.sleep(1)
                exit_status_ready = channel.exit_status_ready()

            while channel.recv_ready():
                print(channel.recv(1024))
            while channel.recv_stderr_ready():
                print(channel.recv_stderr(1024))

            exit_code = channel.recv_exit_status()
            if exit_code != 0:
                raise errors.Error("Bundle deployment failed with exit code: {}".format(exit_code))
        finally:
            channel.close()

    def run_script(self, script):
        sftp = self.open_sftp()
        sftp.chdir(".")

        random_string = binascii.hexlify(os.urandom(4)).decode('ascii')
        path = os.path.join(sftp.getcwd(), 'touchdown_%s' % (random_string))

        try:
            sftp.putfo(script, path)
            sftp.chmod(path, 0o755)
            try:
                transport = self.get_transport()
                self._run(transport, "sudo " + path)
            finally:
                sftp.remove(path)
                pass
        finally:
            sftp.close()

    def verify_transport(self):
        # FIXME: Run a shell command like 'false' and make sure it returns false
        # Then run a shell command like 'whoami' and make sure it has exit code 0 and returns the right user
        # Some weird AMI's hijack SSH a bit and allow authentication to succeed, but then return an error
        # when the user tries to run any command. Great if SSHing in from terminal
        # but rubbish for developers D:
        return

    def connect(self, **kwargs):
        for i in range(self.connection_attempts):
            try:
                super(Client, self).connect(**kwargs)
                break
            except paramiko.PasswordRequiredException:
                raise errors.Error("Unable to authenticate with remote server")
            except (socket.error, EOFError):
                time.sleep(i + 1)
        else:
            raise errors.Error("Unable to connect to remove server after {} tries".format(self.connection_attempts))

        self.verify_transport()
