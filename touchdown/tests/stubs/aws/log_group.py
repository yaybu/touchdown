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


class LogGroupStubber(ServiceStubber):

    client_service = 'logs'

    def add_describe_log_groups_empty_response(self):
        return self.add_response(
            'describe_log_groups',
            service_response={
                'logGroups': [],
            },
            expected_params={
                'logGroupNamePrefix': self.resource.name,
            }
        )

    def add_describe_log_groups_one_response(self):
        return self.add_response(
            'describe_log_groups',
            service_response={
                'logGroups': [{
                    'logGroupName': self.resource.name,
                    'arn': 'arn:log_group:1234:' + self.resource.name,
                }],
            },
            expected_params={
                'logGroupNamePrefix': self.resource.name,
            }
        )

    def add_create_log_group(self):
        return self.add_response(
            'create_log_group',
            service_response={},
            expected_params={
                'logGroupName': self.resource.name,
            }
        )

    def add_put_retention_policy(self, retention):
        return self.add_response(
            'put_retention_policy',
            service_response={},
            expected_params={
                'logGroupName': self.resource.name,
                'retentionInDays': retention,
            }
        )

    def add_delete_log_group(self):
        return self.add_response(
            'delete_log_group',
            service_response={
            },
            expected_params={
                'logGroupName': self.resource.name,
            }
        )
