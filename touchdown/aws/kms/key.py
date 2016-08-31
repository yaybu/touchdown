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

from botocore.exceptions import ClientError

from touchdown.core import argument, errors, serializers
from touchdown.core.plan import Plan
from touchdown.core.resource import Resource

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy


class Key(Resource):

    resource_name = 'key'

    name = argument.String(max=8192, field='Description')
    usage = argument.String(choices=['ENCRYPT_DECRYPT'], default='ENCRYPT_DECRYPT', field='KeyUsage')
    policy = argument.Dict(field='Policy', serializer=serializers.Json())

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = Key
    service_name = 'kms'
    api_version = '2014-11-01'
    describe_action = 'list_keys'
    describe_envelope = 'Keys'
    describe_filters = {}
    key = 'KeyId'

    def create_data_key(self, context=None):
        self.object = self.describe_object()
        response = self.client.generate_data_key(
            KeyId=self.object['KeyId'],
            KeySpec='AES_256',
            EncryptionContext=context or {},
        )
        return response['Plaintext'], response['CiphertextBlob']

    def decrypt_data_key(self, ciphertext_blob, context=None):
        try:
            response = self.client.decrypt(
                CiphertextBlob=ciphertext_blob,
                EncryptionContext=context or {},
            )
        except Exception as e:
            raise errors.Error('Key decryption failed: {}'.format(e))
        return response['Plaintext']

    def describe_object_matches(self, key):
        try:
            metadata = self.client.describe_key(KeyId=key['KeyId'])
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDeniedException':
                return False
            raise

        if not metadata['KeyMetadata']['Enabled']:
            return False

        return metadata['KeyMetadata']['Description'] == self.resource.name


class Apply(SimpleApply, Describe):

    create_action = 'create_key'
    create_envelope = 'KeyMetadata'

    def update_object(self):
        for change in super(Apply, self).update_object():
            yield change

        remote_policy = self.object.get('Policy', None)
        if remote_policy and remote_policy != self.resource.policy:
            yield self.generic_action(
                'Update policy',
                self.client.update_assume_role_policy,
                RoleName=serializers.Identifier(),
                PolicyDocument=serializers.Json(serializers.Argument('policy')),
            )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'schedule_key_deletion'
