# Copyright 2014-2015 Isotoma Limited
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

import base64
import struct

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from paramiko.util import deflate_long

from touchdown.core import argument, serializers
from touchdown.core.plan import XOR, Plan, Present
from touchdown.core.resource import Resource
from touchdown.core.utils import force_bytes, force_str

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy


class PublicKeyFromPrivateKey(serializers.Formatter):

    def render(self, runner, value):
        private_key = serialization.load_pem_private_key(
            force_bytes(value),
            password=None,
            backend=default_backend(),
        )
        numbers = private_key.public_key().public_numbers()

        output = b''
        parts = [b'ssh-rsa', deflate_long(numbers.e), deflate_long(numbers.n)]
        for part in parts:
            output += struct.pack('>I', len(part)) + part
        return force_str(b'ssh-rsa ' + base64.b64encode(output) + b'\n')


class KeyPair(Resource):

    resource_name = 'keypair'

    name = argument.String(field='KeyName')

    public_key = argument.String(field='PublicKeyMaterial')
    private_key = argument.String(
        field='PublicKeyMaterial',
        serializer=PublicKeyFromPrivateKey(),
    )

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = KeyPair
    service_name = 'ec2'
    api_version = '2015-10-01'
    describe_action = 'describe_key_pairs'
    describe_envelope = 'KeyPairs'
    describe_notfound_exception = 'InvalidKeyPair.NotFound'
    key = 'KeyName'

    def get_describe_filters(self):
        return {'KeyNames': [self.resource.name]}


class Apply(SimpleApply, Describe):

    create_action = 'import_key_pair'
    create_response = 'id-only'

    signature = (
        Present('name'),
        XOR(
            Present('public_key'),
            Present('private_key'),
        ),
    )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_key_pair'
