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
from touchdown.tests.stubs.aws import LoadBalancerStubber, Stubber


class TestCreateLoadBalancer(StubberTestCase):

    def test_create_load_balancer(self):
        goal = self.create_goal('apply')

        load_balancer = self.fixtures.enter_context(LoadBalancerStubber(
            goal.get_service(
                self.aws.add_load_balancer(
                    name='test-load_balancer',
                    listeners=[],
                ),
                'apply',
            )
        ))

        load_balancer.add_describe_load_balancers_empty()
        load_balancer.add_create_load_balancer()

        load_balancer.add_describe_load_balancers_one()
        load_balancer.add_describe_load_balancer_attributes()

        load_balancer.add_describe_load_balancers_one()
        load_balancer.add_describe_load_balancer_attributes()

        load_balancer.add_describe_load_balancers_one()
        load_balancer.add_describe_load_balancer_attributes()

        goal.execute()

    def test_create_load_balancer_idempotent(self):
        goal = self.create_goal('apply')

        load_balancer = self.fixtures.enter_context(LoadBalancerStubber(
            goal.get_service(
                self.aws.add_load_balancer(
                    name='test-load_balancer',
                    listeners=[],
                ),
                'apply',
            )
        ))

        load_balancer.add_describe_load_balancers_one()
        load_balancer.add_describe_load_balancer_attributes()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(load_balancer.resource)), 0)


class TestDestroyLoadBalancer(StubberTestCase):

    def test_destroy_load_balancer(self):
        goal = self.create_goal('destroy')

        load_balancer = self.fixtures.enter_context(LoadBalancerStubber(
            goal.get_service(
                self.aws.add_load_balancer(
                    name='test-load_balancer',
                ),
                'destroy',
            )
        ))

        load_balancer.add_describe_load_balancers_one()
        load_balancer.add_describe_load_balancer_attributes()
        load_balancer.add_delete_load_balancer()

        network_interface_waiter = self.fixtures.enter_context(
            Stubber(load_balancer.service.ec2_client)
        )
        network_interface_waiter.add_response(
            'describe_network_interfaces',
            service_response={},
            expected_params={
                'Filters': [{
                    'Name': 'description',
                    'Values': ['ELB test-load_balancer'],
                }],
            },
        )

        goal.execute()

    def test_destroy_load_balancer_idempotent(self):
        goal = self.create_goal('destroy')

        load_balancer = self.fixtures.enter_context(LoadBalancerStubber(
            goal.get_service(
                self.aws.add_load_balancer(
                    name='test-load_balancer',
                ),
                'destroy',
            )
        ))

        load_balancer.add_describe_load_balancers_empty()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(load_balancer.resource)), 0)
