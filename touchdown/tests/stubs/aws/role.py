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


class RoleStubber(ServiceStubber):

    client_service = 'iam'

    def add_list_roles_one_response_by_name(self, assume_role_policy_document=None):
        role = {
            'RoleName': self.resource.name,
            'Path': '/iam/myrole',
            'RoleId': '1234567890123456',
            'Arn': '12345678901234567890',
            'CreateDate': datetime.datetime.now(),
        }

        if assume_role_policy_document:
            role['AssumeRolePolicyDocument'] = assume_role_policy_document

        return self.add_response(
            'list_roles',
            service_response={
                'Roles': [role],
            },
            expected_params={},
        )

    def add_list_roles_empty_response_by_name(self):
        return self.add_response(
            'list_roles',
            service_response={
                'Roles': [],
            },
            expected_params={},
        )

    def add_list_role_policies(self, *policies):
        return self.add_response(
            'list_role_policies',
            service_response={
                'PolicyNames': list(policies),
            },
            expected_params={
                'RoleName': self.resource.name,
            }
        )

    def add_get_role_policy(self, name, policy):
        return self.add_response(
            'get_role_policy',
            service_response={
                'RoleName': self.resource.name,
                'PolicyName': name,
                'PolicyDocument': policy,
            },
            expected_params={
                'RoleName': self.resource.name,
                'PolicyName': name,
            }
        )

    def add_create_role(self, assume_role_policy_document):
        return self.add_response(
            'create_role',
            service_response={
                'Role': {
                    'RoleName': self.resource.name,
                    'Path': '/iam/myrole',
                    'RoleId': '1234567890123456',
                    'Arn': '12345678901234567890',
                    'CreateDate': datetime.datetime.now(),
                },
            },
            expected_params={
                'RoleName': self.resource.name,
                'AssumeRolePolicyDocument': assume_role_policy_document,
            }
        )

    def add_put_role_policy(self, name, policy):
        return self.add_response(
            'put_role_policy',
            service_response={},
            expected_params={
                'RoleName': self.resource.name,
                'PolicyName': name,
                'PolicyDocument': policy,
            }
        )

    def add_delete_role_policy(self, name):
        return self.add_response(
            'delete_role_policy',
            service_response={},
            expected_params={
                'RoleName': self.resource.name,
                'PolicyName': name,
            }
        )

    def add_delete_role(self):
        return self.add_response(
            'delete_role',
            service_response={},
            expected_params={
                'RoleName': self.resource.name,
            }
        )
