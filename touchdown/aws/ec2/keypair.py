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

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from touchdown.core.resource import Resource
from touchdown.core.plan import Plan, Present, XOR
from touchdown.core import argument, serializers

from ..account import BaseAccount
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy


class PublicKeyFromPrivateKey(serializers.Formatter):

    def render(self, runner, value):
        private_key = serialization.load_pem_private_key(
            value,
            password=None,
            backend=default_backend(),
        )
        return private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )


class KeyPair(Resource):

    resource_name = "keypair"

    name = argument.String(field="KeyName")

    public_key = argument.String(field="PublicKeyMaterial")
    private_key = argument.String(
        field="PublicKeyMaterial",
        serializer=PublicKeyFromPrivateKey(),
    )

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = KeyPair
    service_name = 'ec2'
    describe_action = "describe_key_pairs"
    describe_envelope = "KeyPairs"
    describe_notfound_exception = "InvalidKeyPair.NotFound"
    key = 'KeyName'

    def get_describe_filters(self):
        return {"KeyNames": [self.resource.name]}


class Apply(SimpleApply, Describe):

    create_action = "import_key_pair"
    create_response = "id-only"

    signature = (
        Present("name"),
        XOR(
            Present("public_key"),
            Present("private_key"),
        ),
    )


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_key_pair"
