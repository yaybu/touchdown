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


class TestSelectors(StubberTestCase):

    def setUp(self):
        super(TestSelectors, self).setUp()
        self.aws.add_ec2_instance(
            name='my-ec2-instance',
        )
        self.database = self.aws.add_database(
            name='my-database',
            subnet_group=self.aws.add_db_subnet_group(name='my-subnet-group'),
        )
        self.echo = self.workspace.add_echo(text=self.database.endpoint_address)
        self.workspace.load()

    def test_adjacent_outgoing(self):
        self.assertEqual(
            self.workspace.resources.starting_at(self.echo).adjacent_outgoing().get(),
            self.database,
        )

    def test_adjacent_incoming(self):
        self.assertEqual(
            self.workspace.resources.starting_at(self.echo).adjacent_incoming().get(),
            self.workspace,
        )
