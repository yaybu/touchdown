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

from botocore.exceptions import ClientError

from touchdown.aws import common
from touchdown.aws.rds import Database
from touchdown.core import errors, plan


class Plan(common.SimplePlan, plan.Plan):

    name = 'snapshot'
    resource = Database
    service_name = 'rds'
    api_version = '2014-10-31'

    def db_exists(self, name):
        try:
            self.client.describe_db_instances(DBInstanceIdentifier=name)
        except ClientError:
            return False
        return True

    def snapshot_exists(self, target, snapshot_name):
        try:
            result = self.client.describe_db_snapshots(
                DBInstanceIdentifier=target,
                DBSnapshotIdentifier=snapshot_name
            )
        except ClientError as e:
            print(e)
            return False
        return len(result['DBSnapshots']) > 0

    def snapshot(self, snapshot_name):
        if not self.db_exists(self.resource.name):
            raise errors.Error('Database {} does not exist; Nothing to backup'.format(self.resource.name))

        if self.snapshot_exists(self.resource.name, snapshot_name):
            raise errors.Error('Snapshot {} already exists'.format(snapshot_name))

        self.echo('Starting snapshot of {} as {}'.format(self.resource.name, snapshot_name))
        self.client.create_db_snapshot(
            DBSnapshotIdentifier=snapshot_name,
            DBInstanceIdentifier=self.resource.name,
        )

        self.echo('Waiting for snapshot to complete')
        self.client.get_waiter('db_snapshot_completed').wait(
            DBSnapshotIdentifier=snapshot_name,
        )

        self.echo('Snapshot {} available'.format(snapshot_name))
