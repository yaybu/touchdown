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


class PasswordPolicyStubber(ServiceStubber):

    client_service = 'iam'

    def add_get_account_password_policy_empty_response(self):
        return self.add_client_error(
            'get_account_password_policy',
            service_error_code='NoSuchEntity',
            service_message='',
        )

    def add_get_account_password_policy(self):
        return self.add_response(
            'get_account_password_policy',
            service_response={
                'PasswordPolicy': {
                    'AllowUsersToChangePassword': False,
                },
                'ResponseMetadata': {
                    'HTTPStatusCode': 200,
                }
            },
            expected_params={},
        )

    def add_update_account_password_policy(self, **policy):
        return self.add_response(
            'update_account_password_policy',
            service_response={},
            expected_params=policy,
        )

    def add_delete_account_password_policy(self):
        return self.add_response(
            'delete_account_password_policy',
            service_response={},
            expected_params={},
        )
