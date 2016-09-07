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

from touchdown.tests.stubs.aws import VpnGatewayStubber

from .fixture import AwsFixture


class VpnGatewayFixture(AwsFixture):

    def __init__(self, goal, vpc):
        super(VpnGatewayFixture, self).__init__(goal, vpc.account)
        self.vpc = vpc

    def __enter__(self):
        self.vpn_gateway_stubber = self.fixtures.enter_context(VpnGatewayStubber(
            self.goal.get_service(
                self.vpc.get_vpn_gateway(
                    name='test-vpn_gateway',
                ),
                'describe',
            ),
        ))
        self.vpn_gateway_stubber.add_describe_vpn_gateways_one_response()

        self.vpn_gateway = self.vpn_gateway_stubber.resource
        self.vpn_gateway_id = self.vpn_gateway_stubber.make_id(self.vpn_gateway.name)

        return self
