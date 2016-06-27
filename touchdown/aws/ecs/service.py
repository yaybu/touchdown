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

from ..common import SimpleApply, SimpleDescribe, SimpleDestroy
from ..elb import LoadBalancer
from ..iam import Role
from .cluster import Cluster
from .task_definition import TaskDefinition


class LoadBalancerMapping(Resource):

    load_balancer = argument.Resource(LoadBalancer, field='loadBalancerName')
    container_name = argument.String(field='containerName')
    container_port = argument.Integer(field='containerPort')


class Service(Resource):

    resource_name = 'service'

    name = argument.String(field='serviceName', min=1, max=256)
    cluster = argument.Resource(Cluster, field='cluster')
    task = argument.Resource(TaskDefinition, field='taskDefinition')
    desired = argument.Integer(field='desiredCount')
    role = argument.Resource(Role, field='role')
    load_balancers = argument.ResourceList(
        LoadBalancerMapping,
        field='loadBalancers',
        serializer=serializers.List(serializers.Resource(), skip_empty=True),
    )


class Describe(SimpleDescribe, Plan):

    resource = Service
    service_name = 'ecs'
    describe_action = 'describe_services'
    describe_envelope = 'services'
    key = 'serviceName'

    def get_describe_filters(self):
        return {
            'cluster': self.resource.cluster.name,
            'services': [self.resource.name],
        }


class Apply(SimpleApply, Describe):

    create_action = 'create_service'


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_service'
