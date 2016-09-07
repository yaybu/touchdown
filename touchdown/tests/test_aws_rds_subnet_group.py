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
from touchdown.tests.fixtures.aws import SubnetFixture, VpcFixture
from touchdown.tests.stubs.aws import RdsSubnetGroupStubber


class TestSubnetGroupCreation(StubberTestCase):

    def test_create_subnet_group(self):
        goal = self.create_goal('apply')

        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))
        subnet = self.fixtures.enter_context(SubnetFixture(goal, vpcf.vpc))

        subnet_group = self.fixtures.enter_context(RdsSubnetGroupStubber(
            goal.get_service(
                self.aws.add_db_subnet_group(
                    name='my-subnet_group',
                    description='my-subnet-group-description',
                    subnets=[subnet],
                ),
                'apply',
            )
        ))
        subnet_group.add_describe_db_subnet_groups_empty()
        subnet_group.add_create_subnet_group()

        goal.execute()

    def test_create_subnet_group_idempotent(self):
        goal = self.create_goal('apply')

        subnet_group = self.fixtures.enter_context(RdsSubnetGroupStubber(
            goal.get_service(
                self.aws.add_db_subnet_group(
                    name='my-subnet_group',
                ),
                'apply',
            )
        ))
        subnet_group.add_describe_db_subnet_groups_one()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(subnet_group.resource)), 0)


class TestSubnetGroupDeletion(StubberTestCase):

    def test_delete_subnet_group(self):
        goal = self.create_goal('destroy')

        subnet_group = self.fixtures.enter_context(RdsSubnetGroupStubber(
            goal.get_service(
                self.aws.add_db_subnet_group(
                    name='my-subnet_group',
                ),
                'destroy',
            )
        ))
        subnet_group.add_describe_db_subnet_groups_one()
        subnet_group.add_delete_subnet_group()

        goal.execute()

    def test_delete_subnet_group_idempotent(self):
        goal = self.create_goal('destroy')

        subnet_group = self.fixtures.enter_context(RdsSubnetGroupStubber(
            goal.get_service(
                self.aws.add_db_subnet_group(
                    name='my-subnet_group',
                ),
                'destroy',
            )
        ))
        subnet_group.add_describe_db_subnet_groups_empty()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(subnet_group.resource)), 0)
