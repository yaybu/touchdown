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

from .aws import StubberTestCase
from .stubs.aws import VpcStubber


class TestVpcCreation(StubberTestCase):

    def test_create_vpc(self):
        goal = self.create_goal('apply')

        vpc = self.fixtures.enter_context(VpcStubber(
            goal.get_service(
                self.aws.add_vpc(
                    name='test-vpc',
                    cidr_block='192.168.0.0/25',
                ),
                'apply',
            )
        ))

        vpc.add_describe_vpcs_empty_response_by_name()
        vpc.add_create_vpc()
        vpc.add_create_tags(Name='test-vpc')

        # Wait for VPC to exist
        vpc.add_describe_vpcs_empty_response_by_name()

        vpc.add_describe_vpcs_one_response_by_name(state='pending')

        vpc.add_describe_vpcs_one_response_by_name()

        # Check it really does exist, gather more info about it and carry on
        vpc.add_describe_vpcs_one_response_by_name()
        vpc.add_describe_vpc_attributes()

        goal.execute()

    def test_create_vpc_idempotent(self):
        goal = self.create_goal('apply')

        vpc = self.fixtures.enter_context(VpcStubber(
            goal.get_service(
                self.aws.add_vpc(
                    name='test-vpc',
                    cidr_block='192.168.0.0/25',
                ),
                'apply',
            )
        ))

        vpc.add_describe_vpcs_one_response_by_name()
        vpc.add_describe_vpc_attributes()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(vpc.resource)), 0)

    def test_modify_vpc(self):
        goal = self.create_goal('apply')

        vpc = self.fixtures.enter_context(VpcStubber(
            goal.get_service(
                self.aws.add_vpc(
                    name='test-vpc',
                    cidr_block='192.168.0.0/26',
                    enable_dns_support=False,
                    enable_dns_hostnames=True,
                ),
                'apply',
            )
        ))

        vpc.add_describe_vpcs_one_response_by_name()
        vpc.add_describe_vpc_attributes()
        vpc.add_modify_vpc_attributes()

        goal.execute()


class TestVpcDestroy(StubberTestCase):

    def test_destroy_vpc(self):
        goal = self.create_goal('destroy')

        vpc = self.fixtures.enter_context(VpcStubber(
            goal.get_service(
                self.aws.add_vpc(
                    name='test-vpc',
                    cidr_block='192.168.0.0/25',
                ),
                'destroy',
            )
        ))

        vpc.add_describe_vpcs_one_response_by_name()
        vpc.add_describe_vpc_attributes()
        vpc.add_delete_vpc()

        goal.execute()

    def test_destroy_vpc_idempotent(self):
        goal = self.create_goal('destroy')

        vpc = self.fixtures.enter_context(VpcStubber(
            goal.get_service(
                self.aws.add_vpc(
                    name='test-vpc',
                    cidr_block='192.168.0.0/25',
                ),
                'destroy',
            )
        ))

        vpc.add_describe_vpcs_empty_response_by_name()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(vpc.resource)), 0)
