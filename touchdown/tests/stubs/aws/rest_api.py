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


class RestApiStubber(ServiceStubber):

    client_service = 'apigateway'

    def add_get_rest_apis_empty_response(self):
        return self.add_response(
            'get_rest_apis',
            service_response={},
            expected_params={},
        )

    def add_get_rest_apis_one_response(self):
        return self.add_response(
            'get_rest_apis',
            service_response={
                'items': [{
                    'name': self.resource.name,
                    'id': self.make_id(self.resource.name),
                }],
            },
            expected_params={},
        )

    def add_create_rest_api(self):
        return self.add_response(
            'create_rest_api',
            service_response={},
            expected_params={
                'name': self.resource.name,
            }
        )

    def add_delete_rest_api(self):
        return self.add_response(
            'delete_rest_api',
            service_response={},
            expected_params={
                'restApiId': self.make_id(self.resource.name),
            }
        )
