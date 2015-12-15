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

from touchdown.core.plan import Plan
from touchdown.core import resource, argument, serializers
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy

from .rest_api import RestApi
from .resource import Resource


class Method(resource.Resource):

    resource_name = "method"

    name = argument.String(field="httpMethod")
    authorization_type = argument.String(field="authorizationType")
    api_key_required = argument.Boolean(field="apiKeyRequired")

    request_parameters = argument.Dict(field="requestParameters")
    request_models = argument.Dict(field="requestModels")

    resource = argument.Resource(
        Resource,
        field="resourceId",
    )



class Describe(SimpleDescribe, Plan):

    resource = Method
    service_name = 'apigateway'
    describe_action = "get_method"
    describe_envelope = "@"
    key = 'httpMethod'

    def get_describe_filters(self):
        resource = self.runner.get_plan(self.resource.resource)
        if not resource.resource_id:
            return None
        return serializers.Dict(
            restApiId=resource.api.identifier(),
            resourceId=resource.identifier(),
            httpMethod=self.resource.method,
        )


class Apply(SimpleApply, Describe):

    create_action = "put_method"
    create_envelope = "@"

    def get_create_serializer(self):
        return serializers.Resource(
            restApiId=self.resource.resource.api.identifier(),
        )


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_method"

    def get_destroy_serializer(self):
        return serializers.Dict(
            restApiId=self.resource.rest_api.identifier(),
            resourceId=self.resource.identifier(),
        )
