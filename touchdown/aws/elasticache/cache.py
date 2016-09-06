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
from touchdown.core.plan import Plan, Present
from touchdown.core.resource import Resource

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy
from ..vpc import SecurityGroup
from .subnet_group import SubnetGroup


class BaseCacheCluster(Resource):

    instance_class = argument.String(field='CacheNodeType', update=False)
    engine = argument.String(field='Engine', update=False)
    engine_version = argument.String(field='EngineVersion')
    port = argument.Integer(min=1, max=32768, field='Port', update=False)
    security_groups = argument.ResourceList(SecurityGroup, field='SecurityGroupIds', update=False)
    availability_zone = argument.String(field='PreferredAvailabilityZone')
    multi_az = argument.Boolean(field='AZMode', serializer=serializers.Expression(lambda r, o: 'cross-az' if o else 'single-az'))
    auto_minor_version_upgrade = argument.Boolean(field='AutoMinorVersionUpgrade', update=False)
    subnet_group = argument.Resource(SubnetGroup, field='CacheSubnetGroupName', update=False)
    # parameter_group = argument.Resource(ParamaterGroup, field='CacheParameterGroupName')
    apply_immediately = argument.Boolean(field='ApplyImmediately', aws_create=False)

    # tags = argument.Dict()
    account = argument.Resource(BaseAccount)


class CacheCluster(BaseCacheCluster):

    resource_name = 'cache_cluster'

    name = argument.String(min=1, max=20, regex=r'^[a-z1-9\-]*$', field='CacheClusterId')
    num_cache_nodes = argument.Integer(default=1, min=1, field='NumCacheNodes')

    # replication_group = argument.Resource('touchdown.aws.elasticache.replication_group.ReplicationGroup', field='ReplicationGroupId')

    endpoint_address = output.Output(serializers.Property('CacheNodes[0].Endpoint.Address'))
    endpoint_port = output.Output(serializers.Property('CacheNodes[0].Endpoint.Port'))


class Describe(SimpleDescribe, Plan):

    resource = CacheCluster
    service_name = 'elasticache'
    api_version = '2015-02-02'
    describe_action = 'describe_cache_clusters'
    describe_notfound_exception = 'CacheClusterNotFound'
    describe_envelope = 'CacheClusters'
    key = 'CacheClusterId'


class Apply(SimpleApply, Describe):

    create_action = 'create_cache_cluster'
    # update_action = 'modify_cache_cluster'
    waiter = 'cache_cluster_available'

    signature = (
        Present('name'),
        Present('instance_class'),
    )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_cache_cluster'
    waiter = 'cache_cluster_deleted'
