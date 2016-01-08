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

from . import aws


class TestSubnet(aws.RecordedBotoCoreTest):

    def test_create_and_delete_subnet(self):
        vpc = self.aws.add_vpc(
            name='test-vpc',
            cidr_block='192.168.0.0/25',
        )
        vpc.add_subnet(
            name='test-subnet',
            cidr_block='192.168.0.0/25',
        )
        self.apply()
        self.destroy()

    def test_adding_and_removing_route_table_to_subnet(self):
        vpc = self.aws.add_vpc(
            name='test-vpc',
            cidr_block='192.168.0.0/25',
        )
        subnet = vpc.add_subnet(
            name='test-subnet',
            cidr_block='192.168.0.0/25',
            route_table=vpc.add_route_table(
                name='test-subnet',
            ),
        )
        self.apply()
        subnet.route_table = None
        self.apply()
        self.destroy()

    def test_adding_and_removing_acls_to_subnet(self):
        vpc = self.aws.add_vpc(
            name='test-vpc',
            cidr_block='192.168.0.0/25',
        )
        subnet = vpc.add_subnet(
            name='test-subnet',
            cidr_block='192.168.0.0/25',
        )
        self.apply()
        subnet.network_acl = vpc.add_network_acl(
            name='test-subnet',
        )
        self.apply()
        self.destroy()
