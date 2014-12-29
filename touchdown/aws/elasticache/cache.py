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

from .subnet_group import SubnetGroup
from .replication_group import ReplicationGroup


class CacheCluster(Resource):

    resource_name = "cache_cluster"

    name = argument.String()

    """ The kind of hardware to use, for example 'db.t1.micro' """
    instance_class = argument.String()

    """ The type of database to use, for example 'postgres' """
    engine = argument.String(default='postgres')

    engine_version = argument.String()

    """ A list of security groups to apply to this instance """
    security_groups = argument.List()

    availability_zone = argument.String()

    subnet_group = argument.Resource(SubnetGroup)

    replication_group = argument.Resource(ReplicationGroup)

    multi_az = argument.Boolean()

    storage_type = argument.String()

    auto_minor_version_upgrade = argument.Boolean()

    tags = argument.Dict()

    account = argument.Resource(AWS)


class AddCacheCluster(Action):

    @property
    def description(self):
        yield "Add cache cluster '{}'".format(self.resource.name)

    def run(self):
        params = {
            "CacheClusterId": self.resource.name,
        }

        if self.resource.replication_group:
            replication_group = self.runner.get_target(self.resource.replication_group)
            params['ReplicationGroupId'] = replication_group.resource_id

        if self.resource.multi_az:
            params['AZMode'] = self.resource.multi_az

        if self.resource.availability_zone:
            params['PreferredAvailabilityZone'] = self.resource.availabilty_zone

        if self.resource.num_cache_nodes:
            params['NumCacheNodes'] = self.resource.num_cache_nodes

        if self.resource.cache_node_type:
            params['CacheNodeType'] = self.resource.cache_node_type

        if self.resource.engine:
            params['Engine'] = self.resource.engine

        if self.resource.engine_version:
            params['EngineVersion'] = self.resource.engine_version

        if self.resurce.parameter_group:
            parameter_group = self.runner.get_target(self.resource.parameter_group)
            params['CacheParameterGroupName'] = parameter_group.reasource_id

        if self.resource.subnet_group:
            subnet_group = self.runner.get_target(self.resource.subnet_group)
            params['CacheSubnetGroupName'] = subnet_group.resource_id

        if self.resource.security_groups:
            # groups = self.runner
            # params['SecurityGroupIds']
            pass

        # params['SnapshortArns']
        # params['SnapshotName']
        # params['PreferredMaintenanceWindow']

        if self.resource.port:
            params['Port'] = self.resource.port

        # params['NotificationTopicArn']
        #
        if self.resource.auto_minor_version_upgrade:
            params['AutoMinorVersionUpgrade'] = self.resource.auto_minor_version_upgrade

        # params['SnapshotRetentionLimit']
        # params['SnapshotWindow']

        result = self.target.client.create_cache_cluster(DryRun=True, **params)
        print result

        waiter = self.target.client.get_waiter("db_instance_available")
        result = waiter.wait(DBInstanceIdentifier=[obj['DBInstanceIdentifier']])
        print result


class Apply(SimpleApply, Target):

    resource = CacheCluster
    add_action = AddCacheCluster
    key = 'DBInstanceIdentifier'

    def get_object(self, runner):
        if self.resource.subnet_group:
            self.client = runner.get_target(self.resource.subnet_group).client
        else:
            account = runner.get_target(self.resource.acount)
            self.client = account.get_client('elasticache')

        try:
            cache_clusters = self.client.describe_cache_clusters(
                CacheClusterId = self.resource.name,
            )
        except Exception as e:
            if e.response['Error']['Code'] == 'CacheClusterNotFound':
                return
            raise

        if len(cache_clusters['CacheClusters']) > 1:
            raise error.Error("Multiple matches for CacheClusters named {}".format(self.resource.name))
        if cache_clusters['CacheClusters']:
            return cache_clusters['CacheClusters'][0]
