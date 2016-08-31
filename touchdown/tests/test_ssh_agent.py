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

import binascii
import os
import socket
import struct
import unittest

from paramiko.common import asbytes
from paramiko.message import Message
from paramiko.py3compat import byte_chr

from touchdown.core.utils import force_bytes
from touchdown.ssh.client import private_key_from_string
from touchdown.tests.fixtures.folder import TemporaryFolder
from touchdown.tests.testcases import WorkspaceTestCase

try:
    from touchdown.ssh.agent import PosixAgentServer
except ImportError:
    PosixAgentServer = None


@unittest.skipUnless(PosixAgentServer, 'requires unix')
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
        self.assertEqual(msg.get_string(), b'id_rsa_test')

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
        self.assertEqual(binascii.hexlify(msg.get_binary()), force_bytes((
            '000000077373682d7273610000010031d4c2bfad183557a7055f005c3d0d838d5'
            '701bd7b8a09d6d7f06699c691842c18e2bb62504a4beba0fbf5aeaf62f8106352'
            'b99f60d1fdc2dac1f5ad29566022eff25f62fac38cb2db849ed6b862af5e6bd36'
            '09b249a099848aa6fcfdfe1d93d2538ab4e614ecc95a4282abf8742c7bb591db9'
            '3e049e70a559d29134d207018a650b77fd9a7b6be8a2b1f75efbd66fa5a1e9e96'
            '3a5245ebe76294e0d150dfa2348bc7303203263b11952f0300e7b3a9efab81827'
            'b9e53d8c1cb8b2a1551c22cbab9e747fcff79bf57373f7ec8cb2a0dc9b42a7264'
            'afa4b7913693b709c5418eda02175b0a183549643127be92e79936ffc91479629'
            'c2acdc6aa5c83250a8edfe'
        )))

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
