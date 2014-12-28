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


class Database(Resource):

    resource_name = "database"

    name = argument.String()
    instance_identifier = argument.String()

    """ The amount of storage to be allocated (in GB). """
    allocated_storage = argument.Integer(min=5, max=3072)

    iops = argument.Integer()

    """ The kind of hardware to use, for example 'db.t1.micro' """
    instance_class = argument.String()

    """ The type of database to use, for example 'postgres' """
    engine = argument.String(default='postgres')

    engine_version = argument.String()

    license_model = argument.String()

    """ The username of the main client user """
    master_username = argument.String()

    """ The password of the main client user """
    master_password = argument.String()

    """ A list of security groups to apply to this instance """
    security_groups = argument.List()

    publically_accessible = argument.Boolean()

    availability_zone = argument.String()

    subnet_group = argument.Resource(SubnetGroup)

    multi_az = argument.Boolean()

    storage_type = argument.String()

    auto_minor_version_upgrade = argument.Boolean()

    tags = argument.Dict()

    account = argument.Resource(AWS)


class AddDatabaseInstance(Action):

    @property
    def description(self):
        yield "Add database instance '{}'".format(self.resource.name)

    def run(self):
        params = {
            "DBInstanceIdentifier": self.resource.name,
            "AllocatedStorage": self.resource.allocated_storage,
            "DBInstanceClass": self.resource.instance_class,
            "Engine": self.resource.engine,
            "MasterUsername": self.resource.master_username,
            "MasterUserPassword": self.resource.master_password,
        }

        if self.resouce.db_name:
            params['DBName'] = self.resource.db_name

        if self.resource.security_groups:
            v = params['VpcSecurityGroupIds'] = []
            for group in self.resource.security_groups:
                pass

        if self.resource.availability_zone:
            params['AvailabilityZone'] = self.resource.availability_zone

        if self.resource.subnet_group:
            subnet_group = runner.get_target(self.resource.subnet_group)
            params['DBSubnetGroupName'] = subnet_group.resource_id

        if self.resource.preferred_maintenance_window:
            params['PreferredMaintenanceWindow'] = self.resource.preferred_maintenance_window

        # if self.resource.paramater_group:
        #     parameter_group = runner.get_target(self.resource.paramter_group)
        #     params['DBParameterGroupName'] = parameter_group


        if self.resource.backup_retention_period:
            params['BackupRetentionPeriod'] = self.resource.backup_retention_period

        if self.resource.preferred_backup_window:
            params['PreferredBackupWindow'] = self.resource.preferred_backup_window

        if self.resource.port:
            params['Port'] = self.resource.port

        if self.resource.multi_az:
            params['MultiAZ'] = self.resource.multi_az

        if self.resource.engine_version:
            params['EngineVersion'] = self.resource.engine_version

        if self.resource.auto_minor_version_upgrade:
            params['AutoMinorVersionUpgrade'] = self.resource.auto_minor_version_upgrade

        if self.resource.license_model:
            params['LicenseModel'] = self.resource.license_model

        if self.resource.iops:
            params['Iops'] = self.resource.iops

        # if self.resource.option_group:
        #     option_group = runner.get_target(self.resource.option_group)
        #     params['OptionGroupName'] = option_group.resource_id

        if self.resource.character_set_name:
            params['CharacterSetName'] = self.resource.character_set_name

        if self.resource.publicly_accessible:
            params['PubliclyAccessible'] = self.resource.publicly_accessible

        if self.resource.storage_type:
            params['StorageType'] = self.resource.storage_type

        result = self.target.client.create_db_instance(DryRun=True, **params)
        print result

        waiter = self.target.client.get_waiter("db_instance_available")
        result = waiter.wait(DBInstanceIdentifier=[obj['DBInstanceIdentifier']])
        print result


class Apply(SimpleApply, Target):

    resource = Database
    add_action = AddDatabaseInstance
    key = 'DBInstanceIdentifier'

    def get_object(self, runner):
        if self.resource.subnet_group:
            self.client = runner.get_target(self.resource.subnet_group).client
        else:
            account = runner.get_target(self.resource.acount)
            self.client = account.get_client('rds')

        try:
            databases = self.client.describe_db_instances(
                DBInstanceIdentifier = self.resource.name,
            )
        except Exception as e:
            if e.response['Error']['Code'] == 'DBInstanceNotFound':
                return
            raise

        if len(databases['DBInstances']) > 1:
            raise error.Error("Multiple matches for DBInstances named {}".format(self.resource.name))
        if databases['DBInstances']:
            return databases['DBInstances'][0]
