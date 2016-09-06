# Copyright 2014 Isotoma Limited
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

from touchdown.core import argument, output, serializers
from touchdown.core.plan import Plan

from ..common import SimpleApply, SimpleDescribe, SimpleDestroy
from .cache import BaseCacheCluster


class ReplicationGroup(BaseCacheCluster):

    resource_name = 'replication_group'

    name = argument.String(max=16, regex=r'[a-z1-9\-]{1,20}', field='ReplicationGroupId')
    description = argument.String(default=lambda resource: resource.name, field='ReplicationGroupDescription')

    primary_cluster = argument.Resource('touchdown.aws.elasticache.cache.CacheCluster', field='PrimaryClusterId')
    automatic_failover = argument.Boolean(field='AutomaticFailoverEnabled')
    num_cache_clusters = argument.Integer(field='NumCacheClusters', update=False)

    endpoint_address = output.Output(serializers.Property('NodeGroups[0].PrimaryEndpoint.Address'))
    endpoint_port = output.Output(serializers.Property('NodeGroups[0].PrimaryEndpoint.Port'))


class Describe(SimpleDescribe, Plan):

    resource = ReplicationGroup
    service_name = 'elasticache'
    api_version = '2015-02-02'
    describe_action = 'describe_replication_groups'
    describe_envelope = 'ReplicationGroups'
    describe_notfound_exception = 'ReplicationGroupNotFoundFault'
    key = 'ReplicationGroupId'


class Apply(SimpleApply, Describe):

    create_action = 'create_replication_group'
    update_action = 'modify_replication_group'
    waiter = 'replication_group_available'


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_replication_group'
    waiter = 'replication_group_deleted'

    def get_destroy_serializer(self):
        return serializers.Dict(
            ReplicationGroupId=serializers.Identifier(),
            RetainPrimaryCluster=True if self.resource.primary_cluster else False,
        )
