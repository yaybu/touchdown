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

from touchdown.core.datetime import now

from .service import ServiceStubber


class AccountStubber(ServiceStubber):

    client_service = 'sts'

    def __init__(self, service):
        self.resource = service.resource
        self.service = service
        # This is deliberately not AccountStubber!!
        super(ServiceStubber, self).__init__(service.base_client)

    def add_get_session_token(self):
        return self.add_response(
            'get_session_token',
            service_response={
                'Credentials': {
                    'AccessKeyId': 'AKIMFAGETSESSIONMFAGETSESSION',
                    'SecretAccessKey': 'abcdefghijklmnopqrstuvwxyzmfa',
                    'SessionToken': 'zyxwvutsrqpnomlkjihgfedcbamfa',
                    'Expiration': now(),
                },
            },
            expected_params={
                'SerialNumber': 'mymfaserial',
                'TokenCode': '123456',
            }
        )
