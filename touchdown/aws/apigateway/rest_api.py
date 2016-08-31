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
from touchdown.core.resource import Resource

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy


class RestApi(Resource):

    resource_name = 'rest_api'

    name = argument.String(field='name')
    description = argument.String(name='description')

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = RestApi
    service_name = 'apigateway'
    api_version = '2015-07-09'
    describe_action = 'get_rest_apis'
    describe_envelope = 'items'
    key = 'id'

    def get_describe_filters(self):
        return {}

    def describe_object_matches(self, obj):
        return self.resource.name == obj.get('name', '')


class Apply(SimpleApply, Describe):

    create_action = 'create_rest_api'
    create_envelope = '@'


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_rest_api'

    def get_destroy_serializer(self):
        return serializers.Dict(
            restApiId=serializers.Identifier(),
        )
