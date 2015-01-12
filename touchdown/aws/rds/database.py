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
from touchdown.core import argument

from ..account import Account
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy

from .subnet_group import SubnetGroup


class Database(Resource):

    resource_name = "database"

    name = argument.String(field="DBInstanceIdentifier")

    db_name = argument.String(field="DBName")
    """ The name of a database to create in the database instance """

    allocated_storage = argument.Integer(min=5, max=3072, field="AllocatedStorage")
    """ The amount of storage to be allocated (in GB). """

    iops = argument.Integer(field="Iops")

    instance_class = argument.String(field="DBInstanceClass")
    """ The kind of hardware to use, for example 'db.t1.micro' """

    engine = argument.String(default='postgres', field="Engine", aws_update=False)
    """ The type of database to use, for example 'postgres' """

    engine_version = argument.String(field="EngineVersion")

    license_model = argument.String()

    master_username = argument.String(field="MasterUsername")
    """ The username of the main client user """

    master_password = argument.String(field="MasterPassword")
    """ The password of the main client user """

    security_groups = argument.List(field="VpcSecurityGroupIds")
    """ A list of security groups to apply to this instance """

    publically_accessible = argument.Boolean(field="PubliclyAccessible", aws_update=False)

    availability_zone = argument.String(field="AvailabilityZone")

    subnet_group = argument.Resource(SubnetGroup, field="DBSubnetGroupName", aws_update=False)

    preferred_maintenance_window = argument.String(field="PreferredMaintenanceWindow")

    multi_az = argument.Boolean(field="MultiAZ")

    storage_type = argument.String(field="StorageType")

    allow_major_version_upgrade = argument.Boolean(field="AllowMajorVersionUpgrade")

    auto_minor_version_upgrade = argument.Boolean(field="AutoMinorVersionUpgrade")

    character_set_name = argument.String(field="CharacterSetName")

    backup_retention_period = argument.Integer(field="BackupRetentionPeriod")

    preferred_backup_window = argument.String(field="PreferredBackupWindow")

    license_model = argument.String(field="LicenseModel")

    port = argument.Integer(min=1, max=32768, field="Port")

    # paramter_group = argument.Resource(ParameterGroup, field="DBParameterGroupName")
    # option_group = argument.Resource(OptionGroup, field="OptionGroupName")

    apply_immediately = argument.Boolean(field="ApplyImmediately", aws_create=False)

    # tags = argument.Dict()

    account = argument.Resource(Account)


class Describe(SimpleDescribe, Target):

    resource = Database
    service_name = 'rds'
    describe_action = "describe_db_instances"
    describe_notfound_exception = "DBInstanceNotFound"
    describe_list_key = "DBInstances"
    key = 'DBInstanceIdentifier'


class Apply(SimpleApply, Describe):

    create_action = "create_db_instance"
    update_action = "modify_db_instance"

    signature = (
        Present("name"),
        Present("allocated_storage"),
        Present("instance_class"),
        Present("engine"),
        Present("master_username"),
        Present("master_password"),
    )


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_db_instance"
