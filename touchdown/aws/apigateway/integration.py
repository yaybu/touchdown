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

from .resource import Resource


class Integration(resource.Resource):

    resource_name = "integration"

    name = argument.String(field="httpMethod")
    integration_type = argument.String(
        choices=['HTTP', 'AWS', 'MOCK'],
        field='type'
    )
    integration_http_method = argument.String(field="integrationHttpMethod")
    request_parameters = argument.Dict(field="requestParameters")
    request_templates = argument.Dict(field="requestTemplates")
    uri = argument.String(field='uri')
    credentials = argument.String(field='credentials')
    cache_namespace = argument.String(field="cacheNamespace")
    cache_key_parameters = argument.List(
        argument.String(),
        field="cacheKeyParameters"
    )

    resource = argument.Resource(
        Resource,
        field="resourceId",
    )


class Describe(SimpleDescribe, Plan):

    resource = Integration
    service_name = 'apigateway'
    describe_action = "get_integration"
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

    create_action = "put_integration"
    create_envelope = "@"

    def get_create_serializer(self):
        return serializers.Resource(
            restApiId=self.resource.resource.api.identifier(),
        )


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_integration"

    def get_destroy_serializer(self):
        return serializers.Dict(
            restApiId=self.resource.rest_api.identifier(),
            resourceId=self.resource.identifier(),
        )
