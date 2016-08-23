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


class EventRuleStubber(ServiceStubber):

    client_service = 'events'

    def add_list_rules_empty_response(self):
        return self.add_response(
            'list_rules',
            service_response={
                'Rules': [],
            },
            expected_params={
                'NamePrefix': self.resource.name,
            },
        )

    def add_list_rules_one_response_by_name(self):
        return self.add_response(
            'list_rules',
            service_response={
                'Rules': [{
                    'Name': self.resource.name,
                }],
            },
            expected_params={
                'NamePrefix': self.resource.name,
            },
        )

    def add_list_targets_by_rule(self, targets):
        return self.add_response(
            'list_targets_by_rule',
            service_response={
                'Targets': targets,
            },
            expected_params={
                'Rule': self.resource.name,
            },
        )

    def add_remove_targets(self, target_ids):
        return self.add_response(
            'remove_targets',
            service_response={
            },
            expected_params={
                'Rule': self.resource.name,
                'Ids': target_ids,
            },
        )

    def add_delete_rule(self):
        return self.add_response(
            'delete_rule',
            service_response={
            },
            expected_params={
                'Name': self.resource.name,
            },
        )
