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

    def validate(self, target, db_name, old_db_name):
        db = self.get_database(db_name)
        if not db:
            raise errors.Error("Database {} not found?".format(db_name))

        if self.get_database(old_db_name):
            raise errors.Error("Database {} already exists - restore in progress?".format(old_db_name))

        try:
            datetime = parse_datetime(target)
            if datetime > db['LatestRestorableTime']:
                raise errors.Error("You cannot restore to {}. The most recent restorable time is {}".format(
                    datetime,
                    db['LatestRestorableTime'],
                ))
            if datetime < db['InstanceCreateTime']:
                raise errors.Error('You cannot restore to {} because it is before the instance was created ({})'.format(
                    datetime,
                    db['InstanceCreateTime'],
                ))
            snapshots = self.client.describe_db_snapshots(DBInstanceIdentifier=db_name).get('DBSnapshots', [])
            snapshots = filter(lambda snapshot: snapshot['InstanceCreateTime'] == db['InstanceCreateTime'], snapshots)
            snapshots.sort(key=lambda snapshot: snapshot['SnapshotCreateTime'])
            if not snapshots or datetime < snapshots[0]['SnapshotCreateTime']:
                raise errors.Error('You cannot restore to {} because it is before the first available backup was created ({})'.format(
                    datetime,
                    snapshots[0]['SnapshotCreateTime'],
                ))

        except ValueError:
            try:
                snapshots = self.client.describe_db_snapshots(DBInstanceIdentifier=db_name, DBSnapshotIdentifier=target).get('DBSnapshots', [])
            except ClientError:
                raise errors.Error("Could not find snapshot {}".format(target))
            if len(snapshots) == 0:
                raise errors.Error("Could not find snapshot {}".format(target))
        return db

    def rollback(self, target):
        db_name = self.resource.name
        old_db_name = "{}-{:%Y%m%d%H%M%S}".format(db_name, now())

        db = self.validate(target, db_name, old_db_name)

        print("Renaming {} to {}".format(db_name, old_db_name))
        self.client.modify_db_instance(
            DBInstanceIdentifier=db_name,
            NewDBInstanceIdentifier=old_db_name,
            ApplyImmediately=True,
        )

        print("Waiting for rename to be completed")
        while True:
            try:
                self.client.get_waiter("db_instance_available").wait(
                    DBInstanceIdentifier=old_db_name,
                )
            except:
                time.sleep(10)
            else:
                break

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

        for i in range(10):
            print("Waiting for database to be ready")
            try:
                self.client.get_waiter("db_instance_available").wait(
                    DBInstanceIdentifier=db_name,
                )
                break
            except Exception as e:
                print(e)
                time.sleep(10)

        kwargs = get_from_jmes(
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

        print("Restoring database settings")
        self.client.modify_db_instance(
            DBInstanceIdentifier=db_name,
            ApplyImmediately=True,
            **kwargs
        )

        print("Waiting for database to be ready")
        self.client.get_waiter("db_instance_available").wait(
            DBInstanceIdentifier=db_name,
        )

        print("Deleting old database")
        self.client.delete_db_instance(
            DBInstanceIdentifier=old_db_name,
            SkipFinalSnapshot=True,
        )
