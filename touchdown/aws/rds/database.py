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
from touchdown.core.target import Target, Present
from touchdown.core.action import Action
from touchdown.core import argument, errors

from touchdown.aws.vpc import Subnet

from ..account import AWS
from ..common import SimpleApply

from .subnet_group import SubnetGroup


class Database(Resource):

    resource_name = "database"

    name = argument.String(aws_field="DBInstanceIdentifier")

    """ The name of a database to create in the database instance """
    db_name = argument.String(aws_field="DBName")

    """ The amount of storage to be allocated (in GB). """
    allocated_storage = argument.Integer(min=5, max=3072, aws_field="AllocatedStorage")

    iops = argument.Integer(aws_field="Iops")

    """ The kind of hardware to use, for example 'db.t1.micro' """
    instance_class = argument.String(aws_field="DBInstanceClass")

    """ The type of database to use, for example 'postgres' """
    engine = argument.String(default='postgres', aws_field="Engine")

    engine_version = argument.String(aws_field="EngineVersion")

    license_model = argument.String()

    """ The username of the main client user """
    master_username = argument.String(aws_field="MasterUsername")

    """ The password of the main client user """
    master_password = argument.String(aws_field="MasterPassword")

    """ A list of security groups to apply to this instance """
    security_groups = argument.List(aws_field="VpcSecurityGroupIds")

    publically_accessible = argument.Boolean(aws_field="PubliclyAccessible")

    availability_zone = argument.String(aws_field="AvailabilityZone")

    subnet_group = argument.Resource(SubnetGroup, aws_field="DBSubnetGroupName")

    preferred_maintenance_window = argument.String(aws_field="PreferredMaintenanceWindow")

    multi_az = argument.Boolean(aws_field="MultiAZ")

    storage_type = argument.String(aws_field="StorageType")

    auto_minor_version_upgrade = argument.Boolean(aws_field="AutoMinorVersionUpgrade")

    character_set_name = argument.String(aws_field="CharacterSetName")

    backup_retention_period = argument.String(aws_field="BackupRetentionPeriod")

    preferred_backup_window = argument.String(aws_field="PreferredBackupWindow")

    license_model = argument.String(aws_field="LicenseModel")

    port = argument.Integer(min=1, max=32768, aws_field="Port")

    # paramter_group = argument.Resource(ParameterGroup, aws_field="DBParameterGroupName")
    # option_group = argument.Resource(OptionGroup, aws_field="OptionGroupName")

    tags = argument.Dict()

    account = argument.Resource(AWS)


class Apply(SimpleApply, Target):

    resource = Database
    create_action = "create_db_instance"
    describe_action = "describe_db_instances"
    describe_list_key = "DBInstances"
    key = 'DBInstanceIdentifier'

    signature = (
        Present("name"),
        Present("allocated_storage"),
        Present("instance_class"),
        Present("engine"),
        Present("master_username"),
        Present("master_password"),
    )

    @property
    def client(self):
        if self.resource.subnet_group:
            return runner.get_target(self.resource.subnet_group).client
        else:
            account = runner.get_target(self.resource.acount)
            return account.get_client('rds')
