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
from .resource import Resource


class MethodResponse(resource.Resource):

    resource_name = 'method_response'

    name = argument.String(field='httpMethod')
    status_code = argument.String(field='statusCode')

    response_parameters = argument.Dict(field='responseParameters')
    response_models = argument.Dict(field='responseModels')

    resource = argument.Resource(
        Resource,
        field='resourceId',
    )


class Describe(SimpleDescribe, Plan):

    resource = MethodResponse
    service_name = 'apigateway'
    api_version = '2015-07-09'
    describe_action = 'get_method_response'
    describe_notfound_exception = 'NotFoundException'
    describe_envelope = '[@]'
    key = 'httpMethod'

    def get_describe_filters(self):
        api = self.runner.get_plan(self.resource.resource.api)
        if not api.resource_id:
            return None
        resource = self.runner.get_plan(self.resource.resource)
        if not resource.resource_id:
            return None
        return {
            'restApiId': api.resource_id,
            'resourceId': resource.resource_id,
            'httpMethod': self.resource.name,
            'statusCode': self.resource.status_code,
        }


class Apply(SimpleApply, Describe):

    create_action = 'put_method_response'
    create_envelope = '@'

    def get_create_serializer(self):
        return serializers.Resource(
            restApiId=self.resource.resource.api.identifier(),
        )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_method_response'

    def get_destroy_serializer(self):
        return serializers.Dict(
            restApiId=self.resource.resource.api.identifier(),
            resourceId=self.resource.identifier(),
        )
