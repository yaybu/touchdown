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

import json

from touchdown.core import argument, serializers
from touchdown.core.plan import Plan, Present
from touchdown.core.resource import Resource

from ..common import SimpleApply, SimpleDescribe, SimpleDestroy
from .function import Function


class Permission(Resource):

    resource_name = 'permission'

    name = argument.String(field='StatementId')
    action = argument.String(field='Action')
    principal = argument.String(field='Principal')
    source_account = argument.String(field='SourceAccount')
    source_arn = argument.String(field='SourceArn')

    function = argument.Resource(
        Function,
        field='FunctionName',
    )


class Describe(SimpleDescribe, Plan):

    resource = Permission
    service_name = 'lambda'
    api_version = '2015-03-31'
    describe_action = 'get_policy'
    describe_notfound_exception = 'ResourceNotFoundException'
    describe_envelope = '[@]'
    key = 'Sid'

    def get_describe_filters(self):
        func = self.runner.get_plan(self.resource.function)
        if not func.resource_id:
            return None
        return {'FunctionName': self.resource.function.name}

    def describe_object(self):
        obj = super(Describe, self).describe_object()
        policy = json.loads(obj.get('Policy', '{}'))

        matching = filter(
            lambda s: s['Sid'] == self.resource.name,
            policy.get('Statement', []),
        )

        if matching:
            return matching[0]

        return {}


class Apply(SimpleApply, Describe):

    create_action = 'add_permission'
    create_envelope = '@'

    signature = (
        Present('name'),
        Present('action'),
        Present('principal'),
    )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'remove_permission'

    def get_destroy_serializer(self):
        return serializers.Dict(
            FunctionName=self.resource.function.name,
            StatementId=serializers.Identifier(),
        )
