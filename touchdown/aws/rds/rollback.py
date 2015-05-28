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

# This code is not currently exposed publically. It is an example of how to
# stream from a aws log using the FilterLogEvents API.

import time

import jmespath
from botocore.exceptions import ClientError

from touchdown.core import plan, errors
from touchdown.core.datetime import parse_datetime, now
from touchdown.aws import common
from touchdown.aws.rds import Database


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

    name = "rollback"
    resource = Database
    service_name = "rds"

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
            raise errors.Error("Could not find snapshot {}".format(snapshot_name))
        if len(snapshots) == 0:
            raise errors.Error("Could not find snapshot {}".format(snapshot_name))

    def check_point_in_time(self, db, point_in_time):
        # Ensure we don't restore too recently. For example:
        #  1. Obviously we can't restore the future
        #  2. Equally, there is about 5 minutes of replication lag. We can only
        #     restore to periods that were over 5 minutes ago.
        if point_in_time > db['LatestRestorableTime']:
            raise errors.Error("You cannot restore to {}. The most recent restorable time is {}".format(
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
        print("Renaming {} to {}".format(from_name, to_name))
        self.client.modify_db_instance(
            DBInstanceIdentifier=from_name,
            NewDBInstanceIdentifier=to_name,
            ApplyImmediately=True,
        )

    def delete_database(self, name):
        print("Deleting old database")
        self.client.delete_db_instance(
            DBInstanceIdentifier=name,
            SkipFinalSnapshot=True,
        )

    def wait_for_database(self, name):
        print("Waiting for database to be ready")
        while True:
            db = self.get_database(name)
            if db and db['DBInstanceStatus'] == 'available' and len(db['PendingModifiedValues']) == 0:
                return
            time.sleep(10)

    def copy_database_settings(self, db_name, db):
        print("Restoring database settings")
        self.client.modify_db_instance(
            DBInstanceIdentifier=db_name,
            ApplyImmediately=True,
            **get_from_jmes(
                db,
                AllocatedStorage="AllocatedStorage",
                DBSecurityGroups="DBSecurityGroups[?Status == 'active'].DBSecurityGroupName",
                VpcSecurityGroupIds="VpcSecurityGroups[?Status == 'active'].VpcSecurityGroupId",
                DBParameterGroupName="DBParameterGroups[0].DBParameterGroupName",
                BackupRetentionPeriod="BackupRetentionPeriod",
                PreferredBackupWindow="PreferredBackupWindow",
                PreferredMaintenanceWindow="PreferredMaintenanceWindow",
                EngineVersion="EngineVersion",
                CACertificateIdentifier="CACertificateIdentifier",
            )
        )

    def rollback(self, target):
        db_name = self.resource.name
        old_db_name = "{}-{:%Y%m%d%H%M%S}".format(db_name, now())

        db = self.get_database(db_name)
        if not db:
            raise errors.Error("Database {} not found?".format(db_name))

        if self.get_database(old_db_name):
            raise errors.Error("Database {} already exists - restore in progress?".format(old_db_name))

        try:
            datetime_target = parse_datetime(target)
            self.check_point_in_time(db, datetime_target)
        except ValueError:
            self.check_snapshot(db, target)

        self.rename_database(db_name, old_db_name)
        self.wait_for_database(old_db_name)

        kwargs = get_from_jmes(
            db,
            DBInstanceClass="DBInstanceClass",
            Port="Endpoint.Port",
            AvailabilityZone=lambda: "AvailabilityZone" if not db.get('MultiAZ', False) else None,
            DBSubnetGroupName="DBSubnetGroup.DBSubnetGroupName",
            MultiAZ="MultiAZ",
            PubliclyAccessible="PubliclyAccessible",
            AutoMinorVersionUpgrade="AutoMinorVersionUpgrade",
            LicenseModel="LicenseModel",
            DBName=lambda: "DBName" if db["Engine"] != 'postgres' else None,
            Engine="Engine",
            Iops="Iops",
            OptionGroupName="OptionGroupMemberships[0].OptionGroupName",
            StorageType="StorageType",
            TdeCredentialArn="TdeCredentialArn",
        )

        print("Spinning database up from backup")
        if target:
            self.client.restore_db_instance_to_point_in_time(
                SourceDBInstanceIdentifier=old_db_name,
                TargetDBInstanceIdentifier=db_name,
                RestoreTime=target,
                **kwargs
            )
        else:
            self.client.restore_db_instance_from_db_snapshot(
                DBInstanceIdentifier=db_name,
                DBSnapshotIdentifier=target,
                **kwargs
            )

        self.wait_for_database(db_name)

        self.copy_database_settings(db_name, db)
        self.wait_for_database(db_name)

        self.delete_database(old_db_name)
