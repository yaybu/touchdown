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
from touchdown.core.errors import InvalidParameter
from touchdown.core.plan import Plan, Present
from touchdown.core.resource import Resource

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy
from ..kms import Key
from ..vpc import SecurityGroup
from .subnet_group import SubnetGroup


class Database(Resource):

    resource_name = 'database'
    field_order = ['name', 'instance_class', 'storage_encrypted']

    name = argument.String(field='DBInstanceIdentifier')
    db_name = argument.String(field='DBName')
    allocated_storage = argument.Integer(min=5, max=3072, field='AllocatedStorage')
    iops = argument.Integer(field='Iops')
    instance_class = argument.String(field='DBInstanceClass')
    engine = argument.String(default='postgres', field='Engine', update=False)
    engine_version = argument.String(field='EngineVersion')
    license_model = argument.String()
    master_username = argument.String(field='MasterUsername')
    master_password = argument.String(field='MasterUserPassword')
    security_groups = argument.ResourceList(SecurityGroup, field='VpcSecurityGroupIds', update=False)
    publically_accessible = argument.Boolean(field='PubliclyAccessible', update=False)
    availability_zone = argument.String(field='AvailabilityZone')
    subnet_group = argument.Resource(SubnetGroup, field='DBSubnetGroupName', update=False)
    preferred_maintenance_window = argument.String(field='PreferredMaintenanceWindow')
    multi_az = argument.Boolean(field='MultiAZ')
    storage_type = argument.String(field='StorageType', choices=['standard', 'gp2', 'io1'])
    storage_encrypted = argument.Boolean(default=False, field='StorageEncrypted')
    key = argument.Resource(Key, field='KmsKeyId')
    allow_major_version_upgrade = argument.Boolean(field='AllowMajorVersionUpgrade')
    auto_minor_version_upgrade = argument.Boolean(field='AutoMinorVersionUpgrade')
    character_set_name = argument.String(field='CharacterSetName')
    backup_retention_period = argument.Integer(field='BackupRetentionPeriod')
    preferred_backup_window = argument.String(field='PreferredBackupWindow')
    license_model = argument.String(field='LicenseModel')
    port = argument.Integer(min=1, max=32768, field='Port')
    # paramter_group = argument.Resource(ParameterGroup, field='DBParameterGroupName')
    # option_group = argument.Resource(OptionGroup, field='OptionGroupName')
    apply_immediately = argument.Boolean(field='ApplyImmediately', aws_create=False)
    # tags = argument.Dict()
    account = argument.Resource(BaseAccount)

    endpoint_address = output.Output(serializers.Property('Endpoint.Address'))

    def clean_storage_encrypted(self, value):
        if not value:
            return False
        supported_instances = [
            'db.m4.large',
            'db.m4.xlarge',
            'db.m4.2xlarge',
            'db.m4.4xlarge',
            'db.m4.10xlarge',
            'db.m3.medium',
            'db.m3.large',
            'db.m3.xlarge',
            'db.m3.2xlarge',
            'db.r3.large',
            'db.r3.xlarge',
            'db.r3.2xlarge',
            'db.r3.4xlarge',
            'db.r3.8xlarge',
            'db.t2.large',
        ]
        if self.instance_class not in supported_instances:
            raise InvalidParameter('Encryption-at-rest is only supported for a subset of instance classes (such as db.m3.medium)')
        return True


class Describe(SimpleDescribe, Plan):

    resource = Database
    service_name = 'rds'
    api_version = '2014-10-31'
    describe_action = 'describe_db_instances'
    describe_notfound_exception = 'DBInstanceNotFound'
    describe_envelope = 'DBInstances'
    key = 'DBInstanceIdentifier'


class Apply(SimpleApply, Describe):

    create_action = 'create_db_instance'
    # update_action = 'modify_db_instance'
    waiter = 'db_instance_available'

    signature = (
        Present('name'),
        Present('allocated_storage'),
        Present('instance_class'),
        Present('engine'),
        Present('master_username'),
        Present('master_password'),
    )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_db_instance'
    waiter = 'db_instance_deleted'

    def get_destroy_serializer(self):
        return serializers.Dict(
            DBInstanceIdentifier=self.resource_id,
            SkipFinalSnapshot=True,
        )
