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


class QueueStubber(ServiceStubber):

    client_service = 'sqs'

    def add_get_queue_url(self):
        return self.add_response(
            'get_queue_url',
            service_response={
                'QueueUrl': 'https://' + self.resource.name,
            },
            expected_params={
                'QueueName': self.resource.name,
            },
        )

    def add_get_queue_url_404(self):
        return self.add_client_error(
            'get_queue_url',
            service_error_code='AWS.SimpleQueueService.NonExistentQueue',
            service_message='',
        )

    def add_get_queue_attributes(self):
        return self.add_response(
            'get_queue_attributes',
            service_response={
                'Attributes': {},
            },
            expected_params={
                'AttributeNames': ['All'],
                'QueueUrl': 'https://' + self.resource.name,
            },
        )

    def add_create_queue(self):
        return self.add_response(
            'create_queue',
            service_response={
                'QueueUrl': 'https://' + self.resource.name,
            },
            expected_params={
                'QueueName': self.resource.name,
            }
        )

    def add_delete_queue(self):
        return self.add_response(
            'delete_queue',
            service_response={
            },
            expected_params={
                'QueueUrl': 'https://' + self.resource.name,
            }
        )
