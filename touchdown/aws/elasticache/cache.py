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

from ..account import AWS
from ..common import SimpleApply

from .subnet_group import SubnetGroup


class BaseCacheCluster(object):

    """ The name of the cache cluster. Stored as a lowercase string """
    name = argument.String(regex=r"[a-z1-9\-]{1,20}", aws_field="CacheClusterId")

    """ The kind of hardware to use, for example 'db.t1.micro' """
    instance_class = argument.String()

    """ The type of database to use, for example 'postgres' """
    engine = argument.String(default='postgres', aws_field='Engine', aws_update=False)

    """ The version of the cache engine to run """
    engine_version = argument.String(aws_field='EngineVersion')

    """ The TCP/IP port to listen on. """
    port = argument.Integer(min=1, max=32768, aws_field='Port', aws_update=False)

    """ A list of security groups to apply to this instance """
    security_groups = argument.List(aws_field='SecurityGroups')

    """ The preferred availability zone to start this CacheCluster in """
    availability_zone = argument.String(aws_field='PreferredAvailabilityZone')

    """ Whether or not to enable mutli-availability-zone features """
    multi_az = argument.Boolean(aws_field='AZMode')

    """ Automatically deploy cache minor server upgrades """
    auto_minor_version_upgrade = argument.Boolean(aws_field='AutoMinorVersionUpgrade')

    """ The number of nodes to run in this cache cluster """
    num_cache_nodes = argument.Integer(aws_field='NumCacheNodes')

    """ The subnets to start the cache cluster in """
    subnet_group = argument.Resource(SubnetGroup, aws_field='CacheSubnetGroupName')

    # parameter_group = argument.Resource(ParamaterGroup, aws_field='CacheParameterGroupName')

    apply_immediately = argument.Boolean(aws_field="ApplyImmediately", aws_create=False)

    tags = argument.Dict()

    account = argument.Resource(AWS)


class CacheCluster(BaseCacheCluster, Resource):

    resource_name = "cache_cluster"

    # replication_group = argument.Resource("touchdown.aws.elasticache.replication_group.ReplicationGroup", aws_field='ReplicationGroupId')


class Apply(SimpleApply, Target):

    resource = CacheCluster
    create_action = "create_cache_cluster"
    update_action = "modify_cache_cluster"
    describe_action = "describe_cache_clusters"
    describe_notfound_exception = "CacheClusterNotFound"
    describe_list_key = "CacheClusters"
    key = 'CacheClusterId'

    @property
    def client(self):
        if self.resource.subnet_group:
            return self.runner.get_target(self.resource.subnet_group).client
        else:
            account = self.runner.get_target(self.resource.account)
            return account.get_client('elasticache')
