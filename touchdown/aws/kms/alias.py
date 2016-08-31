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

from touchdown.core import argument
from touchdown.core.plan import Plan
from touchdown.core.resource import Resource

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy
from .key import Key


class Alias(Resource):

    resource_name = 'alias'

    name = argument.String(max=256, field='Name')
    key = argument.Resource(Key, field='TargetKeyId')

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = Alias
    service_name = 'kms'
    api_version = '2014-11-01'
    describe_action = 'list_aliases'
    describe_envelope = 'Aliases'
    describe_filters = {}
    key = 'AliasName'

    def describe_object_matches(self, role):
        return role['AliasName'] == self.resource.name


class Apply(SimpleApply, Describe):

    create_action = 'create_alias'

    def update_object(self):
        # FIXME: Can't update an Alias so need to Delete it and then recreate it
        return []


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_alias'
