# Copyright 2015 Isotoma Limited
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

from touchdown.core import argument, serializers
from touchdown.core.plan import Plan

from .account import BaseAccount
from .common import Resource, SimpleApply, SimpleDescribe, SimpleDestroy


class PasswordPolicy(Resource):

    resource_name = 'password_policy'

    min_password_length = argument.Integer(field='MinimumPasswordLength')
    require_symbols = argument.Boolean(field='RequireSymbols')
    require_numbers = argument.Boolean(field='RequireNumbers')
    require_uppercase = argument.Boolean(field='RequireUppercaseCharacters')
    require_lowercase = argument.Boolean(field='RequireLowercaseCharacters')

    allow_users_to_change_password = argument.Boolean(field='AllowUsersToChangePassword')

    expire_passwords = argument.Boolean(field='ExpirePasswords')
    max_password_age = argument.Integer(field='MaxPasswordAge')
    password_reuse_prevention = argument.Integer(field='PasswordReusePrevention', min=1, max=24)
    hard_expiry = argument.Boolean(field='HardExpiry')

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = PasswordPolicy
    service_name = 'iam'
    api_version = '2010-05-08'
    describe_action = 'get_account_password_policy'
    describe_notfound_exception = 'NoSuchEntity'
    describe_envelope = '[PasswordPolicy]'
    key = ''

    def get_describe_filters(self):
        return {}

    signature = []


class Apply(SimpleApply, Describe):

    create_action = 'update_account_password_policy'
    create_response = 'not-that-useful'
    update_action = 'update_account_password_policy'
    waiter = 'account_password_policy_exists'


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_account_password_policy'

    def get_destroy_serializer(self):
        return serializers.Const({})
