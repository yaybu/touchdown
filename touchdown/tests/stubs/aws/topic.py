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


class TopicStubber(ServiceStubber):

    client_service = 'sns'

    def add_list_topics_empty_response(self):
        return self.add_response(
            'list_topics',
            service_response={
                'Topics': [],
            },
            expected_params={
            }
        )

    def add_list_topics_one_response(self):
        return self.add_response(
            'list_topics',
            service_response={
                'Topics': [{
                    'TopicArn': 'arn:topic:1234:' + self.resource.name,
                }],
            },
            expected_params={
            }
        )

    def add_list_subscriptions_by_topic(self, subscriptions=None):
        return self.add_response(
            'list_subscriptions_by_topic',
            service_response={
                'Subscriptions': subscriptions or [],
            },
            expected_params={
                'TopicArn': 'arn:topic:1234:' + self.resource.name,
            }
        )

    def add_get_topic_attributes(self):
        return self.add_response(
            'get_topic_attributes',
            service_response={
                'Attributes': {},
            },
            expected_params={
                'TopicArn': 'arn:topic:1234:' + self.resource.name,
            }
        )

    def add_create_topic(self):
        return self.add_response(
            'create_topic',
            service_response={
                'TopicArn': 'arn:topic:1234:' + self.resource.name,
            },
            expected_params={
                'Name': self.resource.name,
            }
        )

    def add_delete_topic(self):
        return self.add_response(
            'delete_topic',
            service_response={
            },
            expected_params={
                'TopicArn': 'arn:topic:1234:' + self.resource.name,
            }
        )
