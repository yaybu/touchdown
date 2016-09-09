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

import datetime

from .service import ServiceStubber


class InstanceProfileStubber(ServiceStubber):

    client_service = 'iam'

    def add_list_instance_profile_empty_response(self):
        self.add_response(
            'list_instance_profiles',
            service_response={'InstanceProfiles': []},
            expected_params={}
        )

    def add_list_instance_profile_one_response(self):
        self.add_response(
            'list_instance_profiles',
            service_response={'InstanceProfiles': [
                {
                    'Path': '/',
                    'InstanceProfileName': self.resource.name,
                    'InstanceProfileId': self.make_id(self.resource.name),
                    'Arn': self.make_id(self.resource.name),
                    'CreateDate': datetime.datetime.now(),
                    'Roles': [{
                        'RoleName': 'my-test-role',
                        'RoleId': self.make_id(self.resource.name),
                        'Path': '/',
                        'Arn': self.make_id(self.resource.name),
                        'CreateDate': datetime.datetime.now(),
                    }],
                },
            ]},
            expected_params={}
        )

    def add_create_instance_profile(self):
        self.add_response(
            'create_instance_profile',
            service_response={'InstanceProfile': {
                'Path': '/',
                'InstanceProfileName': self.resource.name,
                'InstanceProfileId': self.make_id(self.resource.name),
                'Arn': self.make_id(self.resource.name),
                'CreateDate': datetime.datetime.now(),
                'Roles': [],
                }},
            expected_params={'InstanceProfileName': self.resource.name}
        )

    def add_delete_instance_profile(self):
        self.add_response(
            'delete_instance_profile',
            service_response={},
            expected_params={'InstanceProfileName': self.resource.name}
        )

    def add_add_role_to_instance_profile(self):
        self.add_response(
            'add_role_to_instance_profile',
            service_response={},
            expected_params={'InstanceProfileName': self.resource.name,
                             'RoleName': 'my-test-role'}
        )

    def add_remove_role_from_instance_profile(self):
        self.add_response(
            'remove_role_from_instance_profile',
            service_response={},
            expected_params={'InstanceProfileName': self.resource.name,
                             'RoleName': 'my-test-role'}
        )
