# Copyright 2014 Isotoma Limited
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
import struct
import unittest

from paramiko.common import asbytes
from paramiko.message import Message
from paramiko.py3compat import byte_chr

from touchdown.ssh.client import private_key_from_string
from touchdown.tests.fixtures.folder import TemporaryFolder
from touchdown.tests.testcases import WorkspaceTestCase

try:
    from touchdown.ssh.agent import PosixAgentServer
except ImportError:
    PosixAgentServer = None


@unittest.skipUnless(PosixAgentServer, "requires unix")
class TestPosixAgentHandler(WorkspaceTestCase):

    def setUp(self):
        super(TestPosixAgentHandler, self).setUp()
        folder = self.fixtures.enter_context(TemporaryFolder())
        self.socket_path = os.path.join(folder.folder, 'socket')
        self.agent = PosixAgentServer(self.socket_path)
        self.addCleanup(self.agent.listen_stop)
        pkey = private_key_from_string(open(os.path.join(
            os.path.dirname(__file__),
            'assets',
            'id_rsa_test',
        ), 'r').read())

        self.agent.add(pkey, 'id_rsa_test')
        self.agent.listen_start()

        self.client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.addCleanup(self.client.close)
        self.client.connect(self.socket_path)

    def send(self, msg):
        msg = asbytes(msg)
        self.client.send(struct.pack('>I', len(msg)) + msg)
        size = struct.unpack('>I', self.client.recv(4))[0]
        msg = Message(self.client.recv(size))
        return ord(msg.get_byte()), msg

    def test_handle_11(self):
        # Test handling a SSH2_AGENTC_REQUEST_IDENTITIES
        msg = Message()
        msg.add_byte(byte_chr(11))
        mtype, msg = self.send(msg)
        self.assertEqual(mtype, 12)
        # There should be one identity in the list
        self.assertEqual(msg.get_int(), 1)
        # It should be our identity
        pkey, comment = list(self.agent.identities.values())[0]
        self.assertEqual(msg.get_binary(), pkey.asbytes())
        self.assertEqual(msg.get_string(), comment)

    def test_handle_13(self):
        # Test handling a SSH2_AGENTC_SIGN_REQUEST
        msg = Message()
        # Please sign some data
        msg.add_byte(byte_chr(13))
        # The id of the key to sign with
        key = list(self.agent.identities.values())[0][0].asbytes()
        msg.add_int(len(key))
        msg.add_bytes(bytes(key))
        # A blob of binary to sign
        blob = b'\x0e' * 10
        msg.add_int(len(blob))
        msg.add_bytes(blob)
        # Go go go
        mtype, msg = self.send(msg)
        self.assertEqual(mtype, 14)
        self.assertEqual(msg.get_binary(), (
            '\x00\x00\x00\x07ssh-rsa\x00\x00\x01\x001\xd4\xc2\xbf\xad\x185W\xa7'
            '\x05_\x00\\=\r\x83\x8dW\x01\xbd{\x8a\t\xd6\xd7\xf0f\x99\xc6\x91'
            '\x84,\x18\xe2\xbbbPJK\xeb\xa0\xfb\xf5\xae\xafb\xf8\x10cR\xb9\x9f`'
            '\xd1\xfd\xc2\xda\xc1\xf5\xad)V`"\xef\xf2_b\xfa\xc3\x8c\xb2\xdb'
            '\x84\x9e\xd6\xb8b\xaf^k\xd3`\x9b$\x9a\t\x98H\xaao\xcf\xdf\xe1'
            '\xd9=%8\xabNaN\xcc\x95\xa4(*\xbf\x87B\xc7\xbbY\x1d\xb9>\x04\x9ep'
            '\xa5Y\xd2\x914\xd2\x07\x01\x8ae\x0bw\xfd\x9a{k\xe8\xa2\xb1\xf7^'
            '\xfb\xd6o\xa5\xa1\xe9\xe9c\xa5$^\xbev)N\r\x15\r\xfa#H\xbcs\x03 2c'
            '\xb1\x19R\xf00\x0e{:\x9e\xfa\xb8\x18\'\xb9\xe5=\x8c\x1c\xb8\xb2'
            '\xa1U\x1c"\xcb\xab\x9et\x7f\xcf\xf7\x9b\xf5ss\xf7\xec\x8c\xb2\xa0'
            '\xdc\x9bB\xa7&J\xfaKy\x13i;p\x9cT\x18\xed\xa0!u\xb0\xa1\x83T'
            '\x96C\x12{\xe9.y\x93o\xfc\x91G\x96)\xc2\xac\xdcj\xa5\xc82P\xa8'
            '\xed\xfe'
        ))

    def test_handle_13_failure(self):
        # Test handling a SSH2_AGENTC_SIGN_REQUEST (where no identity)
        msg = Message()
        msg.add_byte(byte_chr(13))
        # The id of the key to sign with - in this case it doesn't exist
        key = b'\x0e' * 10
        msg.add_int(len(key))
        msg.add_bytes(bytes(key))
        # A blob of binary to sign
        blob = b'\x0e' * 10
        msg.add_int(len(blob))
        msg.add_bytes(blob)
        mtype, msg = self.send(msg)
        self.assertEqual(mtype, 5)
