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

from touchdown.core.resource import Resource
from touchdown.core.target import Target
from touchdown.core import argument

from ..common import SimpleDescribe, SimpleApply, SimpleDestroy
from .cache import BaseCacheCluster


class ReplicationGroup(BaseCacheCluster, Resource):

    resource_name = "replication_group"

    name = argument.String(regex=r"[a-z1-9\-]{1,20}", aws_field="CacheClusterId")
    primary_cluster = argument.Resource("touchdown.aws.elasticache.cache.CacheCluster", aws_field="PrimaryClusterId")
    automatic_failover = argument.Boolean(aws_field="AutomaticFailoverEnabled")
    num_cache_clusters = argument.Integer(aws_field="NumCacheClusters")


class Describe(SimpleDescribe, Target):

    resource = ReplicationGroup
    service_name = 'elasticache'
    describe_action = "describe_replication_groups"
    describe_list_key = "ReplicationGroups"
    key = 'ReplicationGroupId'


class Apply(SimpleApply, Describe):

    create_action = "create_replication_group"
    update_action = "modify_replication_group"


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_replication_group"
