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
from touchdown.tests.fixtures.aws import VpcFixture
from touchdown.tests.stubs.aws import VpnGatewayStubber


class TestVpnGatewayCreation(StubberTestCase):

    def test_create_vpn_gateway(self):
        goal = self.create_goal('apply')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        vpn_gateway = self.fixtures.enter_context(VpnGatewayStubber(
            goal.get_service(
                vpcf.vpc.add_vpn_gateway(
                    name='test-vpn_gateway',
                ),
                'apply',
            )
        ))
        vpn_gateway.add_describe_vpn_gateways_empty_response()
        vpn_gateway.add_create_vpn_gateway()
        vpn_gateway.add_create_tags(Name='test-vpn_gateway')

        vpn_gateway.add_attach_vpn_gateway(vpc_id=vpcf.vpc_id)

        # Wait for the attachment
        vpn_gateway.add_describe_vpn_gateways_one_response(attachments=[{
            'VpcId': vpcf.vpc_id,
            'State': 'attaching',
        }])
        vpn_gateway.add_describe_vpn_gateways_one_response(attachments=[{
            'VpcId': vpcf.vpc_id,
            'State': 'attached',
        }])

        goal.execute()

    def test_create_vpn_gateway_idempotent(self):
        goal = self.create_goal('apply')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        vpn_gateway = self.fixtures.enter_context(VpnGatewayStubber(
            goal.get_service(
                vpcf.vpc.add_vpn_gateway(
                    name='test-vpn_gateway',
                ),
                'apply',
            )
        ))
        vpn_gateway.add_describe_vpn_gateways_one_response(attachments=[{
            'VpcId': vpcf.vpc_id,
            'State': 'attached',
        }])

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(vpn_gateway.resource)), 0)


class TestVpnGatewayDestroy(StubberTestCase):

    def test_destroy_vpn_gateway(self):
        goal = self.create_goal('destroy')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        vpn_gateway = self.fixtures.enter_context(VpnGatewayStubber(
            goal.get_service(
                vpcf.vpc.add_vpn_gateway(
                    name='test-vpn_gateway',
                ),
                'destroy',
            )
        ))
        vpn_gateway.add_describe_vpn_gateways_one_response()
        vpn_gateway.add_delete_vpn_gateway()

        goal.execute()

    def test_destroy_vpn_gateway_idempotent(self):
        goal = self.create_goal('destroy')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        vpn_gateway = self.fixtures.enter_context(VpnGatewayStubber(
            goal.get_service(
                vpcf.vpc.add_vpn_gateway(
                    name='test-vpn_gateway',
                ),
                'destroy',
            )
        ))
        vpn_gateway.add_describe_vpn_gateways_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(vpn_gateway.resource)), 0)
