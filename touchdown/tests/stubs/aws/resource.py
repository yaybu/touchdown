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


class ResourceStubber(ServiceStubber):

    client_service = 'apigateway'

    def add_get_resources_empty_response(self, rest_api_id):
        return self.add_response(
            'get_resources',
            service_response={},
            expected_params={
                'restApiId': rest_api_id,
            },
        )

    def add_get_resources_one_response(self, rest_api_id):
        return self.add_response(
            'get_resources',
            service_response={
                'items': [{
                    'path': self.resource.name,
                    'id': self.make_id(self.resource.name),
                }],
            },
            expected_params={
                'restApiId': rest_api_id,
            },
        )

    def add_create_resource(self, rest_api_id, parent_id):
        return self.add_response(
            'create_resource',
            service_response={},
            expected_params={
                'pathPart': self.resource.name,
                'restApiId': rest_api_id,
                'parentId': parent_id,
            }
        )

    def add_delete_resource(self, rest_api_id):
        return self.add_response(
            'delete_resource',
            service_response={},
            expected_params={
                'restApiId': rest_api_id,
                'resourceId': self.make_id(self.resource.name),
            }
        )
