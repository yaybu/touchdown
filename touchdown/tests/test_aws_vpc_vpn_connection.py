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
    CustomerGatewayFixture,
    VpcFixture,
    VpnGatewayFixture,
)
from touchdown.tests.stubs.aws import VpnConnectionStubber


class TestVpnConnectionCreation(StubberTestCase):

    def test_create_vpn_connection(self):
        goal = self.create_goal('apply')

        customer_gatewayf = self.fixtures.enter_context(CustomerGatewayFixture(goal, self.aws))
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))
        vpn_gatewayf = self.fixtures.enter_context(VpnGatewayFixture(goal, vpcf.vpc))

        vpn_connection = self.fixtures.enter_context(VpnConnectionStubber(
            goal.get_service(
                vpcf.vpc.add_vpn_connection(
                    name='test-vpn_connection',
                    customer_gateway=customer_gatewayf.customer_gateway,
                    vpn_gateway=vpn_gatewayf.vpn_gateway,
                ),
                'apply',
            )
        ))
        vpn_connection.add_describe_vpn_connections_empty_response()
        vpn_connection.add_create_vpn_connection(
            customer_gateway_id=customer_gatewayf.customer_gateway_id,
            vpn_gateway_id=vpn_gatewayf.vpn_gateway_id,
        )
        vpn_connection.add_create_tags(Name='test-vpn_connection')

        # Wait for the connection to be available
        vpn_connection.add_describe_vpn_connections_one_response(state='pending')
        vpn_connection.add_describe_vpn_connections_one_response(state='pending')
        vpn_connection.add_describe_vpn_connections_one_response()

        # Refresh cache of remote state
        vpn_connection.add_describe_vpn_connections_one_response()

        goal.execute()

    def test_create_vpn_connection_idempotent(self):
        goal = self.create_goal('apply')

        customer_gatewayf = self.fixtures.enter_context(CustomerGatewayFixture(goal, self.aws))
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))
        vpn_gatewayf = self.fixtures.enter_context(VpnGatewayFixture(goal, vpcf.vpc))

        vpn_connection = self.fixtures.enter_context(VpnConnectionStubber(
            goal.get_service(
                vpcf.vpc.add_vpn_connection(
                    name='test-vpn_connection',
                    customer_gateway=customer_gatewayf.customer_gateway,
                    vpn_gateway=vpn_gatewayf.vpn_gateway,
                ),
                'apply',
            )
        ))
        vpn_connection.add_describe_vpn_connections_one_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(vpn_connection.resource)), 0)


class TestVpnConnectionDestroy(StubberTestCase):

    def test_destroy_vpn_connection(self):
        goal = self.create_goal('destroy')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        vpn_connection = self.fixtures.enter_context(VpnConnectionStubber(
            goal.get_service(
                vpcf.vpc.add_vpn_connection(
                    name='test-vpn_connection',
                ),
                'destroy',
            )
        ))
        vpn_connection.add_describe_vpn_connections_one_response()
        vpn_connection.add_delete_vpn_connection()

        vpn_connection.add_describe_vpn_connections_one_response()
        vpn_connection.add_describe_vpn_connections_one_response(state='deleting')
        vpn_connection.add_describe_vpn_connections_one_response(state='deleting')
        vpn_connection.add_describe_vpn_connections_one_response(state='deleted')
        goal.execute()

    def test_destroy_vpn_connection_idempotent(self):
        goal = self.create_goal('destroy')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        vpn_connection = self.fixtures.enter_context(VpnConnectionStubber(
            goal.get_service(
                vpcf.vpc.add_vpn_connection(
                    name='test-vpn_connection',
                ),
                'destroy',
            )
        ))
        vpn_connection.add_describe_vpn_connections_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(vpn_connection.resource)), 0)
