# Copyright 2016 Isotoma Limited
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

from touchdown.core import errors
from touchdown.tests.aws import StubberTestCase
from touchdown.tests.stubs.aws import DatabaseStubber


class TestDatabaseSnapshots(StubberTestCase):

    def test_snapshot_database(self):
        goal = self.create_goal('snapshot')

        database = self.fixtures.enter_context(DatabaseStubber(
            goal.get_service(
                self.aws.add_database(
                    name='my-database',
                    allocated_storage=5,
                    instance_class='db.m3.medium',
                    engine='postgres',
                    master_username='root',
                    master_password='password',
                    storage_encrypted=True,
                ),
                'snapshot',
            )
        ))

        # Database is running
        database.add_describe_db_instances_one()

        # No matching snapshots
        database.add_response(
            'describe_db_snapshots',
            service_response={
                'DBSnapshots': [],
            },
            expected_params={
                'DBInstanceIdentifier': 'my-database',
                'DBSnapshotIdentifier': 'my-snapshot',
            }
        )

        database.add_response(
            'create_db_snapshot',
            service_response={
            },
            expected_params={
                'DBInstanceIdentifier': 'my-database',
                'DBSnapshotIdentifier': 'my-snapshot',
            }
        )

        # Waiting for snapshot to be available
        database.add_response(
            'describe_db_snapshots',
            service_response={
                'DBSnapshots': [{
                    'DBSnapshotIdentifier': 'snap-12335',
                    'Status': 'not-ready',
                }],
            },
            expected_params={
                'DBSnapshotIdentifier': 'my-snapshot',
            }
        )

        # Finish waiting for snapshot
        database.add_response(
            'describe_db_snapshots',
            service_response={
                'DBSnapshots': [{
                    'DBSnapshotIdentifier': 'snap-12335',
                    'Status': 'available',
                }],
            },
            expected_params={
                'DBSnapshotIdentifier': 'my-snapshot',
            }
        )

        goal.execute('my-database', 'my-snapshot')

    def test_snapshot_database_no_database(self):
        goal = self.create_goal('snapshot')

        database = self.fixtures.enter_context(DatabaseStubber(
            goal.get_service(
                self.aws.add_database(
                    name='my-database',
                    allocated_storage=5,
                    instance_class='db.m3.medium',
                    engine='postgres',
                    master_username='root',
                    master_password='password',
                    storage_encrypted=True,
                ),
                'snapshot',
            )
        ))

        # Database is not running
        database.add_describe_db_instances_empty()

        self.assertRaises(errors.Error, goal.execute, 'my-database', 'my-snapshot')
