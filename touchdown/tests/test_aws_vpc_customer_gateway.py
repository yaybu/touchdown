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
from touchdown.tests.stubs.aws import CustomerGatewayStubber


class TestCustomerGatewayCreation(StubberTestCase):

    def test_create_customer_gateway(self):
        goal = self.create_goal('apply')

        customer_gateway = self.fixtures.enter_context(CustomerGatewayStubber(
            goal.get_service(
                self.aws.add_customer_gateway(
                    name='test-customer_gateway',
                    public_ip='8.8.8.8',
                ),
                'apply',
            )
        ))
        customer_gateway.add_describe_customer_gateways_empty_response()
        customer_gateway.add_create_customer_gateway()
        customer_gateway.add_create_tags(Name='test-customer_gateway')

        # The botocore waiter waits for it to transition to an available state
        customer_gateway.add_describe_customer_gateways_one_response(state='pending')
        customer_gateway.add_describe_customer_gateways_one_response(state='pending')
        customer_gateway.add_describe_customer_gateways_one_response(state='available')

        # It ends up calling it a few more times to refresh some metadata.
        customer_gateway.add_describe_customer_gateways_one_response()

        goal.execute()

    def test_create_customer_gateway_idempotent(self):
        goal = self.create_goal('apply')

        customer_gateway = self.fixtures.enter_context(CustomerGatewayStubber(
            goal.get_service(
                self.aws.add_customer_gateway(
                    name='test-customer_gateway',
                    public_ip='8.8.8.8',
                ),
                'apply',
            )
        ))
        customer_gateway.add_describe_customer_gateways_one_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(customer_gateway.resource)), 0)


class TestCustomerGatewayDestroy(StubberTestCase):

    def test_destroy_customer_gateway(self):
        goal = self.create_goal('destroy')

        customer_gateway = self.fixtures.enter_context(CustomerGatewayStubber(
            goal.get_service(
                self.aws.add_customer_gateway(
                    name='test-customer_gateway',
                    public_ip='8.8.8.8',
                ),
                'destroy',
            )
        ))
        customer_gateway.add_describe_customer_gateways_one_response()
        customer_gateway.add_delete_customer_gateway()

        goal.execute()

    def test_destroy_customer_gateway_idempotent(self):
        goal = self.create_goal('destroy')

        customer_gateway = self.fixtures.enter_context(CustomerGatewayStubber(
            goal.get_service(
                self.aws.add_customer_gateway(
                    name='test-customer_gateway',
                    public_ip='8.8.8.8',
                ),
                'destroy',
            )
        ))
        customer_gateway.add_describe_customer_gateways_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(customer_gateway.resource)), 0)
