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


class Cluster(Resource):

    resource_name = 'ecs_cluster'

    name = argument.String(field='clusterName', min=1, max=256)
    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = Cluster
    service_name = 'ecs'
    describe_action = 'describe_clusters'
    describe_envelope = 'clusters'
    key = 'clusterName'

    def get_describe_filters(self):
        return {'clusters': [self.resource.name]}


class Apply(SimpleApply, Describe):

    create_action = 'create_cluster'


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_cluster'

    def get_destroy_serializer(self):
        # Some of the API's take `clusterName` as an argument, but this isn't
        # one of them - override the parameters to `delete_cluster`...
        return serializers.Dict(cluster=self.resource.name)
