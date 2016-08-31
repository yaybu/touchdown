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

from touchdown.core import argument, resource, serializers
from touchdown.core.plan import Plan

from ..common import SimpleApply, SimpleDescribe, SimpleDestroy
from .rest_api import RestApi


class Resource(resource.Resource):

    resource_name = 'resource'

    name = argument.String(field='pathPart')

    parent_resource = argument.Resource(
        'touchdown.aws.apigateway.resource.Resource',
        field='parentId',
    )
    api = argument.Resource(
        RestApi,
        field='restApiId'
    )


class Describe(SimpleDescribe, Plan):

    resource = Resource
    service_name = 'apigateway'
    api_version = '2015-07-09'
    describe_action = 'get_resources'
    describe_envelope = 'items'
    key = 'id'

    def get_describe_filters(self):
        api = self.runner.get_plan(self.resource.api)
        if not api.resource_id:
            return None
        return {
            'restApiId': api.resource_id,
        }

    def describe_object_matches(self, obj):
        return self.resource.name == obj.get('path', '')


class Apply(SimpleApply, Describe):

    create_action = 'create_resource'
    create_envelope = '@'


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_resource'

    def get_destroy_serializer(self):
        return serializers.Dict(
            restApiId=self.resource.api.identifier(),
            resourceId=self.resource.identifier(),
        )

    def can_delete(self):
        return self.resource.name != '/'
