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


class KeyPairStubber(ServiceStubber):

    client_service = 'ec2'

    def add_describe_keypairs_empty_response_by_name(self):
        return self.add_response(
            'describe_key_pairs',
            service_response={
                'KeyPairs': [],
            },
            expected_params={
                'KeyNames': [self.resource.name],
            }
        )

    def add_describe_keypairs_one_response_by_name(self):
        return self.add_response(
            'describe_key_pairs',
            service_response={
                'KeyPairs': [{
                    'KeyName': self.resource.name,
                }],
            },
            expected_params={
                'KeyNames': [self.resource.name],
            }
        )

    def add_import_key_pair(self, public_key):
        return self.add_response(
            'import_key_pair',
            service_response={
                'KeyName': self.resource.name,
            },
            expected_params={
                'KeyName': self.resource.name,
                'PublicKeyMaterial': public_key,
            }
        )

    def add_delete_key_pair(self):
        return self.add_response(
            'delete_key_pair',
            service_response={},
            expected_params={
                'KeyName': self.resource.name,
            }
        )
