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


class Deployment(resource.Resource):

    resource_name = 'deployment'

    name = argument.String(field='description')
    stage_name = argument.String(field='stageName')
    stage_description = argument.String(field='stageDescription')

    cache_cluster_enabled = argument.Boolean(field='cacheClusterEnabled')
    cache_cluster_size = argument.String(field='cacheClusterSize')

    variables = argument.Dict(field='variables')

    api = argument.Resource(
        RestApi,
        field='restApiId'
    )


class Describe(SimpleDescribe, Plan):

    resource = Deployment
    service_name = 'apigateway'
    api_version = '2015-07-09'
    describe_action = 'get_deployments'
    describe_envelope = 'items'
    key = 'id'

    def get_describe_filters(self):
        api = self.runner.get_plan(self.resource.api)
        if not api.resource_id:
            return None
        return serializers.Dict(
            restApiId=api.identifier(),
        )

    def describe_object_matches(self, obj):
        return self.resource.name == obj.get('description', '')


class Apply(SimpleApply, Describe):

    create_action = 'create_deployment'
    create_envelope = '@'


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_deployment'

    def get_destroy_serializer(self):
        return serializers.Dict(
            restApiId=self.resource.api.identifier(),
            deploymentId=self.resource.identifier(),
        )
