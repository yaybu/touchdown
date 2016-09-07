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


class S3FileStubber(ServiceStubber):

    client_service = 's3'

    def add_list_objects_empty_response(self):
        return self.add_response(
            'list_objects',
            service_response={
            },
            expected_params={
                'Bucket': self.resource.bucket.name
            },
        )

    def add_list_objects_one_response(self):
        return self.add_response(
            'list_objects',
            service_response={
                'Contents': [{
                    'Key': self.resource.name,
                }],
            },
            expected_params={
                'Bucket': self.resource.bucket.name
            },
        )

    def add_put_object(self):
        return self.add_response(
            'put_object',
            service_response={},
            expected_params={
                'Key': self.resource.name,
                'Bucket': self.resource.bucket.name,
                'Body': 'my-test-content',
                'ACL': 'private',
            },
        )

    def add_delete_object(self):
        return self.add_response(
            'delete_object',
            service_response={},
            expected_params={
                'Key': self.resource.name,
                'Bucket': self.resource.bucket.name,
            },
        )
