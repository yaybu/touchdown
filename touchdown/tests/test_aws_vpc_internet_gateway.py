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
from .fixtures.aws import VpcFixture
from .stubs.aws import InternetGatewayStubber


class TestInternetGatewayCreation(StubberTestCase):

    def test_create_internet_gateway(self):
        goal = self.create_goal('apply')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        internet_gateway = self.fixtures.enter_context(InternetGatewayStubber(
            goal.get_service(
                vpcf.vpc.add_internet_gateway(
                    name='test-internet_gateway',
                ),
                'apply',
            )
        ))

        internet_gateway.add_describe_internet_gateways_empty_response()
        internet_gateway.add_create_internet_gateway()
        internet_gateway.add_create_tags(Name='test-internet_gateway')
        internet_gateway.add_attach_internet_gateway(vpc_id=vpcf.vpc_id)

        goal.execute()

    def test_create_internet_gateway_idempotent(self):
        goal = self.create_goal('apply')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        internet_gateway = self.fixtures.enter_context(InternetGatewayStubber(
            goal.get_service(
                vpcf.vpc.add_internet_gateway(
                    name='test-internet_gateway',
                ),
                'apply',
            )
        ))

        internet_gateway.add_describe_internet_gateways_one_response(
            vpc_ids=[vpcf.vpc_id],
        )

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(internet_gateway.resource)), 0)


class TestInternetGatewayDestroy(StubberTestCase):

    def test_destroy_internet_gateway(self):
        goal = self.create_goal('destroy')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        internet_gateway = self.fixtures.enter_context(InternetGatewayStubber(
            goal.get_service(
                vpcf.vpc.add_internet_gateway(
                    name='test-internet_gateway',
                ),
                'destroy',
            )
        ))

        internet_gateway.add_describe_internet_gateways_one_response()
        internet_gateway.add_delete_internet_gateway()

        goal.execute()

    def test_destroy_internet_gateway_idempotent(self):
        goal = self.create_goal('destroy')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        internet_gateway = self.fixtures.enter_context(InternetGatewayStubber(
            goal.get_service(
                vpcf.vpc.add_internet_gateway(
                    name='test-internet_gateway',
                ),
                'destroy',
            )
        ))

        internet_gateway.add_describe_internet_gateways_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(internet_gateway.resource)), 0)
