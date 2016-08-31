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
from .deployment import Deployment


class Stage(resource.Resource):

    resource_name = 'stage'

    name = argument.String(field='stageName')
    description = argument.String(field='description')

    cache_cluster_enabled = argument.Boolean(field='cacheClusterEnabled')
    cache_cluster_size = argument.String(field='cacheClusterSize')

    variables = argument.Dict(field='variables')

    deployment = argument.Resource(
        Deployment,
        field='deploymentId',
    )


class Describe(SimpleDescribe, Plan):

    resource = Stage
    service_name = 'apigateway'
    api_version = '2015-07-09'
    describe_action = 'get_stages'
    describe_envelope = 'item'  # This is not a typo
    key = 'id'

    def get_describe_filters(self):
        deployment = self.runner.get_plan(self.resource.deployment)
        if not deployment.resource_id:
            return None
        return serializers.Dict(
            restApiId=deployment.api.identifier(),
            deploymentId=deployment.identifier(),
        )

    def describe_object_matches(self, obj):
        return self.resource.name == obj.get('stageName', '')


class Apply(SimpleApply, Describe):

    create_action = 'create_resource'
    create_envelope = '@'

    def get_create_serializer(self):
        return serializers.Resource(
            restApidId=self.resource.stage.api.identifier(),
        )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_resource'

    def get_destroy_serializer(self):
        return serializers.Dict(
            restApiId=self.resource.stage.api.identifier(),
            stageName=self.resource.name,
        )
