# Copyright 2015 Isotoma Limited
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

import time

import jmespath
from botocore.exceptions import ClientError

from touchdown.aws import common
from touchdown.aws.rds import Database
from touchdown.core import errors, plan
from touchdown.core.datetime import now, parse_datetime


def get_from_jmes(db, **kwargs):
    new_kwargs = {}
    for key, value in kwargs.items():
        if callable(value):
            value = value()
        if value:
            newval = jmespath.search(value, db)
            if newval:
                new_kwargs[key] = newval
    return new_kwargs


class Plan(common.SimplePlan, plan.Plan):

    name = 'rollback'
    resource = Database
    service_name = 'rds'
    api_version = '2014-10-31'

    def get_database(self, name):
        try:
            dbs = self.client.describe_db_instances(DBInstanceIdentifier=name).get('DBInstances', [])
        except ClientError:
            return None
        return dbs[0]

    def check_snapshot(self, db, snapshot_name):
        try:
            snapshots = self.client.describe_db_snapshots(
                DBInstanceIdentifier=db['DBInstanceIdentifier'],
                DBSnapshotIdentifier=snapshot_name
            ).get('DBSnapshots', [])
        except ClientError:
            raise errors.Error('Could not find snapshot {}'.format(snapshot_name))
        if len(snapshots) == 0:
            raise errors.Error('Could not find snapshot {}'.format(snapshot_name))

    def check_point_in_time(self, db, point_in_time):
        # Ensure we don't restore too recently. For example:
        #  1. Obviously we can't restore the future
        #  2. Equally, there is about 5 minutes of replication lag. We can only
        #     restore to periods that were over 5 minutes ago.
        if point_in_time > db['LatestRestorableTime']:
            raise errors.Error('You cannot restore to {}. The most recent restorable time is {}'.format(
                point_in_time,
                db['LatestRestorableTime'],
            ))

        # Ensure we don't restore before this instance even existed
        if point_in_time < db['InstanceCreateTime']:
            raise errors.Error('You cannot restore to {} because it is before the instance was created ({})'.format(
                point_in_time,
                db['InstanceCreateTime'],
            ))

        # We can't restore earlier than the oldest backup either
        # With a caveat that InstanceIdentifier might imply a snapshot belongs
        # to the current database when it doesn't. We filter on matching
        # InstanceCreateTime to avoid that.
        results = self.client.describe_db_snapshots(
            DBInstanceIdentifier=db['DBInstanceIdentifier']
        )
        snapshots = filter(
            lambda snapshot: snapshot['InstanceCreateTime'] == db['InstanceCreateTime'],
            results.get('DBSnapshots', [])
        )
        snapshots.sort(key=lambda snapshot: snapshot['SnapshotCreateTime'])
        if not snapshots or point_in_time < snapshots[0]['SnapshotCreateTime']:
            raise errors.Error('You cannot restore to {} because it is before the first available backup was created ({})'.format(
                point_in_time,
                snapshots[0]['SnapshotCreateTime'],
            ))

    def rename_database(self, from_name, to_name):
        print('Renaming {} to {}'.format(from_name, to_name))
        self.client.modify_db_instance(
            DBInstanceIdentifier=from_name,
            NewDBInstanceIdentifier=to_name,
            ApplyImmediately=True,
        )

    def delete_database(self, name):
        print('Deleting old database')
        self.client.delete_db_instance(
            DBInstanceIdentifier=name,
            SkipFinalSnapshot=True,
        )

    def wait_for_database(self, name):
        print('Waiting for database to be ready')
        while True:
            db = self.get_database(name)
            if db and db['DBInstanceStatus'] == 'available' and len(db['PendingModifiedValues']) == 0:
                return
            time.sleep(10)

    def copy_database_settings(self, db_name, db):
        print('Restoring database settings')
        self.client.modify_db_instance(
            DBInstanceIdentifier=db_name,
            ApplyImmediately=True,
            **get_from_jmes(
                db,
                AllocatedStorage='AllocatedStorage',
                DBSecurityGroups='DBSecurityGroups[?Status == \'active\'].DBSecurityGroupName',
                VpcSecurityGroupIds='VpcSecurityGroups[?Status == \'active\'].VpcSecurityGroupId',
                DBParameterGroupName='DBParameterGroups[0].DBParameterGroupName',
                BackupRetentionPeriod='BackupRetentionPeriod',
                PreferredBackupWindow='PreferredBackupWindow',
                PreferredMaintenanceWindow='PreferredMaintenanceWindow',
                EngineVersion='EngineVersion',
                CACertificateIdentifier='CACertificateIdentifier',
            )
        )

    def check(self, target):
        self.old_db_name = '{}-{:%Y%m%d%H%M%S}'.format(self.resource.name, now())

        self.db = self.get_database(self.resource.name)
        if not self.db:
            raise errors.Error('Database {} not found?'.format(self.resource.name))

        if self.get_database(self.old_db_name):
            raise errors.Error('Database {} already exists - restore in progress?'.format(self.old_db_name))

        self.datetime_target = None
        try:
            self.datetime_target = parse_datetime(target)
            self.check_point_in_time(self.db, self.datetime_target)
        except errors.Error:
            self.check_snapshot(self.db, target)

    def rollback(self, target):
        self.rename_database(self.resource.name, self.old_db_name)
        self.wait_for_database(self.old_db_name)

        kwargs = get_from_jmes(
            self.db,
            DBInstanceClass='DBInstanceClass',
            Port='Endpoint.Port',
            AvailabilityZone=lambda: 'AvailabilityZone' if not self.db.get('MultiAZ', False) else None,
            DBSubnetGroupName='DBSubnetGroup.DBSubnetGroupName',
            MultiAZ='MultiAZ',
            PubliclyAccessible='PubliclyAccessible',
            AutoMinorVersionUpgrade='AutoMinorVersionUpgrade',
            LicenseModel='LicenseModel',
            DBName=lambda: 'DBName' if self.db['Engine'] != 'postgres' else None,
            Engine='Engine',
            Iops='Iops',
            OptionGroupName='OptionGroupMemberships[0].OptionGroupName',
            StorageType='StorageType',
            TdeCredentialArn='TdeCredentialArn',
        )

        print('Spinning database up from backup')
        if self.datetime_target:
            self.client.restore_db_instance_to_point_in_time(
                SourceDBInstanceIdentifier=self.old_db_name,
                TargetDBInstanceIdentifier=self.resource.name,
                RestoreTime=self.datetime_target,
                **kwargs
            )
        else:
            self.client.restore_db_instance_from_db_snapshot(
                DBInstanceIdentifier=self.resource.name,
                DBSnapshotIdentifier=target,
                **kwargs
            )

        self.wait_for_database(self.resource.name)

        self.copy_database_settings(self.resource.name, self.db)
        self.wait_for_database(self.resource.name)

        self.delete_database(self.old_db_name)
