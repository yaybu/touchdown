# Copyright 2016 John Carr
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
from ..iam import Role


class ScalableTarget(Resource):

    resource_name = 'scalable_target'

    name = argument.Callable(lambda r: ':'.join((r.resource, r.scalable_dimension)))

    service = argument.String(field='ServiceNamespace')
    resource = argument.String(field='ResourceId')
    scalable_dimension = argument.String(field='ScalableDimension')
    min_capacity = argument.Integer(field='MinCapacity')
    max_capacity = argument.Integer(field='MinCapacity')
    role = argument.Resource(Role, field='RoleARN')

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = ScalableTarget
    service_name = 'application-autoscaling'
    api_version = '2016-02-06'
    describe_action = 'describe_scalable_targets'
    describe_envelope = 'ScalableTargets'
    key = 'ResourceId'

    signature = ()

    def get_describe_filters(self):
        return {
            'ServiceNamespace': self.resource.service,
            'ResourceIds': [self.resource.resource],
            'ScalableDimension': self.resource.scalable_dimension,
        }


class Apply(SimpleApply, Describe):

    create_action = 'register_scalable_target'
    create_response = 'not-that-useful'

    signature = ()


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'deregister_scalable_target'

    def get_destroy_serializer(self):
        # Some of the API's take `clusterName` as an argument, but this isn't
        # one of them - override the parameters to `delete_cluster`...
        return serializers.Dict(
            ServiceNamespace=self.resource.service,
            ResourceId=self.resource.resource,
            ScalableDimension=self.resource.scalable_dimension,
        )
