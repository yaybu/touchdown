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

from __future__ import print_function

import binascii
import os
import socket
import sys
import time

import six
import paramiko

from touchdown.core import errors


def private_key_from_string(private_key):
    for cls in (paramiko.RSAKey, paramiko.ECDSAKey, paramiko.DSSKey):
        try:
            f = six.StringIO(private_key)
            key = cls.from_private_key(f)
        except paramiko.SSHException:
            continue
        return key
    raise paramiko.SSHException('not a valid private key file')


class Client(paramiko.SSHClient):

    connection_attempts = 20
    input_encoding = "utf-8"

    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)
        self.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def _run(self, transport, command, input_encoding=None, stdout=None):
        if stdout is None:
            stdout = sys.stdout

        if input_encoding is None:
            input_encoding = self.input_encoding

        def d(data):
            return data.decode(input_encoding, 'replace')

        channel = transport.open_session()
        try:
            channel.exec_command(command)

            # We don't want a stdin
            channel.makefile('wb', -1).close()

            # FIXME: It would be better to block with select
            exit_status_ready = channel.exit_status_ready()
            while not exit_status_ready:
                while channel.recv_ready():
                    print(d(channel.recv(1024)), file=stdout, end='')
                while channel.recv_stderr_ready():
                    print(d(channel.recv_stderr(1024)), file=stdout, end='')
                time.sleep(1)
                exit_status_ready = channel.exit_status_ready()

            buf = d(channel.recv(1024))
            while buf:
                print(buf, file=stdout, end='')
                buf = d(channel.recv(1024))
            print(d(channel.in_buffer.empty()), file=stdout, end='')

            buf = d(channel.recv_stderr(1024))
            while buf:
                print(buf, file=stdout, end='')
                buf = d(channel.recv_stderr(1024))
            print(d(channel.in_stderr_buffer.empty()), file=stdout, end='')

            exit_code = channel.recv_exit_status()
            if exit_code != 0:
                raise errors.RemoteCommandFailed(exit_code)
        finally:
            channel.close()

    def run_script(self, script, sudo=True):
        sftp = self.open_sftp()
        sftp.chdir(".")

        random_string = binascii.hexlify(os.urandom(4)).decode('ascii')
        path = os.path.join(sftp.getcwd(), 'touchdown_%s' % (random_string))

        try:
            sftp.putfo(script, path)
            sftp.chmod(path, 0o755)
            try:
                transport = self.get_transport()
                cmd = path
                if sudo:
                    cmd = "sudo " + path
                self._run(transport, cmd)
            finally:
                sftp.remove(path)
                pass
        finally:
            sftp.close()

    def check_output(self, command):
        result_buf = six.StringIO()
        self._run(self.get_transport(), command, stdout=result_buf)
        return 0, result_buf.getvalue(), ""

    def verify_transport(self):
        # Some weird AMI's hijack SSH a bit and allow authentication to succeed, but then return an error
        # when the user tries to run any command. Great if SSHing in from terminal
        # but rubbish for developers D:

        # FIXME: Run a shell command like 'false' and make sure it returns false

        try:
            whoami = self.check_output('whoami')[1].strip()
        except errors.RemoteCommandFailed:
            raise errors.Error("Unable to selftest SSH connection (whoami failed)")

        if whoami != self.get_transport().get_username():
            raise errors.Error(
                "Tried to connect as {}, but ended up connected as {}".format(
                    self.get_transport().get_username(),
                    whoami,
                )
            )

    def set_input_encoding(self):
        try:
            lang = self.check_output('printenv LANG')[1]
        except errors.RemoteCommandFailed:
            try:
                lang = self.check_output('printenv LC_CTYPE')[1]
            except errors.RemoteCommandFailed:
                lang = 'UTF-8'
        self.input_encoding = lang.rsplit('.', 1)[-1]

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
        self.set_input_encoding()
