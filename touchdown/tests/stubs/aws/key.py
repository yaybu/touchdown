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

from .service import ServiceStubber


class KeyStubber(ServiceStubber):

    client_service = 'kms'

    def add_list_keys_empty(self):
        return self.add_response(
            'list_keys',
            service_response={},
            expected_params={},
        )

    def add_list_keys_one(self):
        return self.add_response(
            'list_keys',
            service_response={
                'Keys': [{
                    'KeyId': self.make_id(self.resource.name),
                    'KeyArn': 'arn:123456:kms:' + self.make_id(self.resource.name),
                }]
            },
            expected_params={},
        )

    def add_describe_key(self):
        return self.add_response(
            'describe_key',
            service_response={
                'KeyMetadata': {
                    'KeyId': self.make_id(self.resource.name),
                    'Description': self.resource.name,
                    'Enabled': True,
                }
            },
            expected_params={
                'KeyId': self.make_id(self.resource.name),
            },
        )

    def add_create_key(self):
        return self.add_response(
            'create_key',
            service_response={
                'KeyMetadata': {
                    'KeyId': self.make_id(self.resource.name),
                }
            },
            expected_params={
                'Description': 'test-key',
                'KeyUsage': 'ENCRYPT_DECRYPT',
                'Policy': '{}',
            },
        )

    def add_schedule_key_deletion(self):
        return self.add_response(
            'schedule_key_deletion',
            service_response={},
            expected_params={
                'KeyId': self.make_id(self.resource.name),
            }
        )

    def add_generate_data_key(self):
        return self.add_response(
            'generate_data_key',
            service_response={
                'CiphertextBlob': b'0' * 32,
                'Plaintext': b'1' * 32,
            },
            expected_params={
                'KeyId': self.make_id(self.resource.name),
                'KeySpec': 'AES_256',
                'EncryptionContext': {},
            },
        )

    def add_decrypt(self):
        return self.add_response(
            'decrypt',
            service_response={
                'Plaintext': b'1' * 32,
            },
            expected_params={
                'CiphertextBlob': b'0' * 32,
                'EncryptionContext': {},
            },
        )
