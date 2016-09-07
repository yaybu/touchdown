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

from touchdown.tests.stubs.aws import CustomerGatewayStubber

from .fixture import AwsFixture


class CustomerGatewayFixture(AwsFixture):

    def __enter__(self):
        self.customer_gateway_stubber = self.fixtures.enter_context(CustomerGatewayStubber(
            self.goal.get_service(
                self.aws.get_customer_gateway(
                    name='test-vpc',
                    public_ip='8.8.8.8',
                ),
                'describe',
            ),
        ))
        self.customer_gateway_stubber.add_describe_customer_gateways_one_response()

        self.customer_gateway = self.customer_gateway_stubber.resource
        self.customer_gateway_id = self.customer_gateway_stubber.make_id(self.customer_gateway.name)

        return self
