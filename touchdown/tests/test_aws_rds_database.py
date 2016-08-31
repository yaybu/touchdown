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

from touchdown.tests.aws import StubberTestCase
from touchdown.tests.stubs.aws import DatabaseStubber


class TestDatabaseCreation(StubberTestCase):

    def test_create_database(self):
        goal = self.create_goal('apply')

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
                'apply',
            )
        ))
        database.add_describe_db_instances_empty()
        database.add_create_db_instance()

        database.add_describe_db_instances_one()
        database.add_describe_db_instances_one()

        goal.execute()

    def test_create_database_idempotent(self):
        goal = self.create_goal('apply')

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
                'apply',
            )
        ))
        database.add_describe_db_instances_one()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(database.resource)), 0)


class TestDatabaseDeletion(StubberTestCase):

    def test_delete_database(self):
        goal = self.create_goal('destroy')

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
                'destroy',
            )
        ))
        database.add_describe_db_instances_one()
        database.add_delete_db_instance()
        database.add_describe_db_instances_empty()

        goal.execute()

    def test_delete_database_idempotent(self):
        goal = self.create_goal('destroy')

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
                'destroy',
            )
        ))
        database.add_describe_db_instances_empty()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(database.resource)), 0)
