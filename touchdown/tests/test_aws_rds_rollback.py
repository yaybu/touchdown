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

import datetime

import mock

from touchdown.tests.aws import StubberTestCase
from touchdown.tests.stubs.aws import DatabaseStubber


class TestDatabaseRollback(StubberTestCase):

    def test_rollback_database_to_snapshot(self):
        goal = self.create_goal('rollback')

        now = self.fixtures.enter_context(mock.patch('touchdown.aws.rds.rollback.now'))
        now.return_value = datetime.datetime(2016, 9, 15, 12, 0, 0)

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
                'rollback',
            )
        ))

        # Database is running
        database.add_response(
            'describe_db_instances',
            service_response={
                'DBInstances': [{
                    'DBInstanceIdentifier': 'my-database',
                    'DBInstanceStatus': 'available',
                    'PendingModifiedValues': {},
                    'Engine': 'postgres',
                    'PubliclyAccessible': True,
                    'MultiAZ': True,
                    'DBSubnetGroup': {
                        'DBSubnetGroupName': 'database-subnet',
                    },
                    'Endpoint': {
                        'Port': 8000,
                    },
                    'DBSecurityGroups': [{
                        'DBSecurityGroupName': 'mysecuritygroup',
                        'Status': 'active',
                    }],
                    'AllocatedStorage': 1000,
                    'DBParameterGroups': [{
                        'DBParameterGroupName': 'some-really-good-parameters'
                    }],
                    'CACertificateIdentifier': 'really-secure-certificates',
                }],
            },
            expected_params={
                'DBInstanceIdentifier': 'my-database',
            }
        )

        # It picks a name to rename the existing database to and checks it isn't in use
        database.add_client_error(
            'describe_db_instances',
            service_error_code='NotFound',
        )

        # Is 'my-snapshot' a snapshot we can use?
        database.add_response(
            'describe_db_snapshots',
            service_response={
                'DBSnapshots': [{
                    'DBSnapshotIdentifier': 'snap-12335',
                    'Status': 'available',
                }],
            },
            expected_params={
                'DBInstanceIdentifier': 'my-database',
                'DBSnapshotIdentifier': 'my-snapshot',
            }
        )

        # Move the existing database out of the way
        database.add_response(
            'modify_db_instance',
            service_response={},
            expected_params={
                'ApplyImmediately': True,
                'DBInstanceIdentifier': 'my-database',
                'NewDBInstanceIdentifier': 'my-database-20160915120000',
            }
        )

        # Wait for old database to be out of the way
        database.add_response(
            'describe_db_instances',
            service_response={
                'DBInstances': [{
                    'DBInstanceIdentifier': 'my-database-20160915120000',
                    'DBInstanceStatus': 'available',
                    'PendingModifiedValues': {},
                }],
            },
            expected_params={
                'DBInstanceIdentifier': 'my-database-20160915120000',
            }
        )

        # OK: Actually restore an instance from the snapshot
        database.add_response(
            'restore_db_instance_from_db_snapshot',
            service_response={},
            expected_params={
                'DBInstanceIdentifier': 'my-database',
                'DBSnapshotIdentifier': 'my-snapshot',
                'DBSubnetGroupName': 'database-subnet',
                'Engine': 'postgres',
                'MultiAZ': True,
                'Port': 8000,
                'PubliclyAccessible': True,
            }
        )

        # Wait for the new database to be ready...
        database.add_response(
            'describe_db_instances',
            service_response={
                'DBInstances': [{
                    'DBInstanceIdentifier': 'my-database',
                    'DBInstanceStatus': 'available',
                    'PendingModifiedValues': {},
                }],
            },
            expected_params={
                'DBInstanceIdentifier': 'my-database',
            }
        )

        # And then change its settings again. This is because you can't choose
        # them all on the restore API call!!!!!!
        database.add_response(
            'modify_db_instance',
            service_response={},
            expected_params={
                'AllocatedStorage': 1000,
                'ApplyImmediately': True,
                'CACertificateIdentifier': 'really-secure-certificates',
                'DBInstanceIdentifier': 'my-database',
                'DBParameterGroupName': 'some-really-good-parameters',
                'DBSecurityGroups': ['mysecuritygroup'],
            }
        )

        # Wait for the new database to be ready...
        database.add_response(
            'describe_db_instances',
            service_response={
                'DBInstances': [{
                    'DBInstanceIdentifier': 'my-database',
                    'DBInstanceStatus': 'available',
                    'PendingModifiedValues': {},
                }],
            },
            expected_params={
                'DBInstanceIdentifier': 'my-database',
            }
        )

        # Now delete the old database...
        database.add_response(
            'delete_db_instance',
            service_response={},
            expected_params={
                'DBInstanceIdentifier': 'my-database-20160915120000',
                'SkipFinalSnapshot': True,
            }
        )

        goal.execute('my-database', 'my-snapshot')
