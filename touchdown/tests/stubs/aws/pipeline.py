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


class PipelineStubber(ServiceStubber):

    client_service = 'elastictranscoder'

    def add_list_pipelines_empty_response(self):
        return self.add_response(
            'list_pipelines',
            service_response={},
            expected_params={},
        )

    def add_list_pipelines_one_response(self, notifications=None):
        return self.add_response(
            'list_pipelines',
            service_response={
                'Pipelines': [{
                    'Name': self.resource.name,
                    'Id': self.make_id(self.resource.name),
                    'Notifications': notifications or {},
                }]
            },
            expected_params={},
        )

    def add_create_pipeline(self, input_bucket, role):
        return self.add_response(
            'create_pipeline',
            service_response={
                'Pipeline': {
                    'Id': self.make_id(self.resource.name),
                },
            },
            expected_params={
                'Name': self.resource.name,
                'InputBucket': input_bucket,
                'Role': role,
            }
        )

    def add_delete_pipeline(self):
        return self.add_response(
            'delete_pipeline',
            service_response={},
            expected_params={
                'Id': self.make_id(self.resource.name),
            }
        )
