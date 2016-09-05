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

import mock

from touchdown.config.expressions import pwgen
from touchdown.tests.aws import StubberTestCase
from touchdown.tests.fixtures.folder import TemporaryFolderFixture
from touchdown.tests.stubs.aws import DatabaseStubber, KeyStubber


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


class TestDatabaseComplications(StubberTestCase):

    def test_database_with_config_password(self):
        goal = self.create_goal('apply')

        # have pwgen generate consistent passwords
        secure_random = self.fixtures.enter_context(mock.patch('touchdown.config.expressions.random.SystemRandom'))
        secure_random.return_value.choice.side_effect = lambda x: x[0]

        folder = self.fixtures.enter_context(TemporaryFolderFixture(goal, self.workspace))

        # A pre-existing KMS key that is used to encrypt a locally stored INI file
        key = self.fixtures.enter_context(KeyStubber(
            goal.get_service(
                self.aws.get_key(
                    name='test-key',
                ),
                'describe',
            )
        ))

        # These are the calls from the planning stage - touchdown needs to check
        # it exists and get key metadata before it will allow any changes to
        # be made
        key.add_list_keys_one()
        key.add_describe_key()

        # These are the API calls made when the config setting is encrypted and
        # stored
        key.add_list_keys_one()
        key.add_describe_key()
        key.add_generate_data_key()

        # The password is decrypted again so that it can be passed to the
        # database creation
        key.add_decrypt()

        # We will call decrypt again in the test to make sure the password
        # was saved
        key.add_decrypt()

        # An ini file that is encrypted with KMS and store on disk
        config_file = key.resource.add_cipher(
            file=folder.add_file(name='test.cfg'),
        ).add_ini_file()

        # A password that is generated by SystemRandom helpers and stored
        # in the secrets config the first time a deployment happens
        password_variable = config_file.add_string(
            name='database.password',
            default=pwgen(symbols=True),
            retain_default=True,
        )

        # A database that uses the password created above
        database = self.fixtures.enter_context(DatabaseStubber(
            goal.get_service(
                self.aws.add_database(
                    name='my-database',
                    allocated_storage=5,
                    instance_class='db.m3.medium',
                    engine='postgres',
                    master_username='root',
                    master_password=password_variable,
                    storage_encrypted=True,
                ),
                'apply',
            )
        ))
        database.add_describe_db_instances_empty()
        database.add_create_db_instance(
            password='a' * 28,
        )

        database.add_describe_db_instances_one()
        database.add_describe_db_instances_one()

        goal.execute()

        stored = goal.get_service(password_variable, 'get').execute()

        # Assert that the generated password is remembered by touchdown
        self.assertEqual(stored[0], 'a' * 28)

        # Assert that touchdown considers this config to be 'user set'
        self.assertEqual(stored[1], True)
