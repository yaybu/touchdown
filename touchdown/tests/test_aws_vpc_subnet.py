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

from touchdown.tests.aws import StubberTestCase
from touchdown.tests.fixtures.aws import (
    NetworkAclFixture,
    RouteTableFixture,
    VpcFixture,
)
from touchdown.tests.stubs.aws import SubnetStubber


class TestSubnetCreation(StubberTestCase):

    def test_create_subnet(self):
        goal = self.create_goal('apply')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        subnet = self.fixtures.enter_context(SubnetStubber(
            goal.get_service(
                vpcf.vpc.add_subnet(
                    name='test-subnet',
                    cidr_block='192.168.0.0/25',
                ),
                'apply',
            )
        ))

        subnet.add_describe_subnets_empty_response()
        subnet.add_create_subnet()
        subnet.add_create_tags(Name='test-subnet')

        # Wait for the subnet to exist
        subnet.add_describe_subnets_empty_response()
        subnet.add_describe_subnets_empty_response()
        subnet.add_describe_subnets_one_response()

        # Call describe_object again to make sure remote state is correctly cached
        subnet.add_describe_subnets_one_response()
        subnet.add_describe_network_acls()
        subnet.add_describe_route_tables()

        goal.execute()

    def test_adding_route_table_to_subnet(self):
        goal = self.create_goal('apply')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))
        route_table = self.fixtures.enter_context(RouteTableFixture(goal, self.aws, vpcf.vpc))

        subnet = self.fixtures.enter_context(SubnetStubber(
            goal.get_service(
                vpcf.vpc.add_subnet(
                    name='test-subnet',
                    cidr_block='192.168.0.0/25',
                    route_table=route_table,
                ),
                'apply',
            )
        ))

        subnet.add_describe_subnets_one_response()
        subnet.add_describe_network_acls()
        subnet.add_describe_route_tables()

        subnet.add_associate_route_table('rt-52f2381b')

        goal.execute()

    def test_adding_nacl_table_to_subnet(self):
        goal = self.create_goal('apply')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))
        nacl = self.fixtures.enter_context(NetworkAclFixture(goal, self.aws, vpcf.vpc))

        subnet = self.fixtures.enter_context(SubnetStubber(
            goal.get_service(
                vpcf.vpc.add_subnet(
                    name='test-subnet',
                    cidr_block='192.168.0.0/25',
                    network_acl=nacl,
                ),
                'apply',
            )
        ))

        subnet.add_describe_subnets_one_response()
        subnet.add_describe_network_acls()
        subnet.add_describe_route_tables()

        subnet.add_replace_network_acl_association()

        goal.execute()

    def test_create_subnet_idempotent(self):
        goal = self.create_goal('apply')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        subnet = self.fixtures.enter_context(SubnetStubber(
            goal.get_service(
                vpcf.vpc.add_subnet(
                    name='test-subnet',
                    cidr_block='192.168.0.0/25',
                ),
                'apply',
            )
        ))

        subnet.add_describe_subnets_one_response()
        subnet.add_describe_network_acls()
        subnet.add_describe_route_tables()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(subnet.resource)), 0)


class TestSubnetDestroy(StubberTestCase):

    def test_destroy_subnet(self):
        goal = self.create_goal('destroy')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        subnet = self.fixtures.enter_context(SubnetStubber(
            goal.get_service(
                vpcf.vpc.add_subnet(
                    name='test-subnet',
                    cidr_block='192.168.0.0/25',
                ),
                'destroy',
            )
        ))

        subnet.add_describe_subnets_one_response()
        subnet.add_describe_network_acls()
        subnet.add_describe_route_tables()
        subnet.add_delete_subnet()

        goal.execute()

    def test_destroy_subnet_idempotent(self):
        goal = self.create_goal('destroy')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        subnet = self.fixtures.enter_context(SubnetStubber(
            goal.get_service(
                vpcf.vpc.add_subnet(
                    name='test-subnet',
                    cidr_block='192.168.0.0/25',
                ),
                'destroy',
            )
        ))

        subnet.add_describe_subnets_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(subnet.resource)), 0)
