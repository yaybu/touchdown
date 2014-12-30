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
from touchdown.core.action import Action
from touchdown.core import argument, errors

from touchdown.aws.vpc import Subnet

from ..account import AWS
from ..common import SimpleApply
from .cache import BaseCacheCluster


class ReplicationGroup(BaseCacheCluster, Resource):

    resource_name = "cache_replication_group"

    name = argument.String(regex=r"[a-z1-9\-]{1,20}", aws_field="CacheClusterId")
    # primary_cluster = argument.Resouce("touchdown.aws.elasticache.cache.CacheCluster", aws_field="PrimaryClusterId")
    automatic_failover = argument.Boolean(aws_field="AutomaticFailoverEnabled")


class Apply(SimpleApply, Target):

    resource = ReplicationGroup
    create_action = "create_replication_group"
    describe_action = "describe_replication_groups"
    describe_list_key = "ReplicationGroups"
    key = 'ReplicationGroupId'

    @property
    def client(self):
        return self.runner.get_target(self.resource.account).get_client('elasticache')
