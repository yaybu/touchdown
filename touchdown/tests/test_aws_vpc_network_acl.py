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

import unittest

from touchdown.core import errors
from touchdown.core.workspace import Workspace

from touchdown.tests.aws import StubberTestCase
from touchdown.tests.fixtures.aws import VpcFixture
from touchdown.tests.stubs.aws import NetworkAclStubber


class TestNetworkAclCreation(StubberTestCase):

    def test_create_network_acl(self):
        goal = self.create_goal('apply')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        network_acl = self.fixtures.enter_context(NetworkAclStubber(
            goal.get_service(
                vpcf.vpc.add_network_acl(
                    name='test-network-acl',
                ),
                'apply',
            )
        ))

        network_acl.add_describe_network_acls_empty_response_by_name()
        network_acl.add_describe_network_acls_empty_response_by_name()
        network_acl.add_create_network_acl()
        network_acl.add_create_tags(Name='test-network-acl.1')

        # Wait for it to exist...
        network_acl.add_describe_network_acls_empty_response_by_name()
        network_acl.add_describe_network_acls_empty_response_by_name()
        network_acl.add_describe_network_acls_one_response_by_name()

        # Update local cache of remote state
        network_acl.add_describe_network_acls_one_response_by_name()
        network_acl.add_describe_network_acls_one_response_by_name()
        network_acl.add_describe_network_acls_one_response_by_name()
        network_acl.add_describe_network_acls_one_response_by_name()
        network_acl.add_describe_network_acls_one_response_by_name()

        goal.execute()

    def test_create_network_acl_idempotent(self):
        goal = self.create_goal('apply')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        network_acl = self.fixtures.enter_context(NetworkAclStubber(
            goal.get_service(
                vpcf.vpc.add_network_acl(
                    name='test-network-acl',
                ),
                'apply',
            )
        ))

        network_acl.add_describe_network_acls_one_response_by_name()
        network_acl.add_describe_network_acls_one_response_by_name()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(network_acl.resource)), 0)


class TestNetworkAclDestroy(StubberTestCase):

    def test_destroy_network_acl(self):
        goal = self.create_goal('destroy')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        network_acl = self.fixtures.enter_context(NetworkAclStubber(
            goal.get_service(
                vpcf.vpc.add_network_acl(
                    name='test-network-acl',
                ),
                'destroy',
            )
        ))

        network_acl.add_describe_network_acls_one_response_by_name()
        network_acl.add_describe_network_acls_one_response_by_name()

        network_acl.add_delete_network_acl()

        goal.execute()

    def test_destroy_network_acl_idempotent(self):
        goal = self.create_goal('destroy')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        network_acl = self.fixtures.enter_context(NetworkAclStubber(
            goal.get_service(
                vpcf.vpc.add_network_acl(
                    name='test-network-acl',
                ),
                'destroy',
            )
        ))

        network_acl.add_describe_network_acls_empty_response_by_name()
        network_acl.add_describe_network_acls_empty_response_by_name()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(network_acl.resource)), 0)


class TestNetworkAclRules(unittest.TestCase):

    def setUp(self):
        self.workspace = Workspace()
        self.aws = self.workspace.add_aws(region='eu-west-1')
        self.vpc = self.aws.add_vpc(name='test-vpc')

    def test_simple_rule_with_all_ports(self):
        acl = self.vpc.add_network_acl(
            name='test-acl',
            inbound=[dict(
                network='10.0.0.0/20',
                protocol='tcp',
                port='*',
            )]
        )
        assert acl.inbound[0].port.start == 1
        assert acl.inbound[0].port.end == 65535

    def test_simple_rule_with_single_port(self):
        acl = self.vpc.add_network_acl(
            name='test-acl',
            inbound=[dict(
                network='10.0.0.0/20',
                protocol='tcp',
                port=20,
            )]
        )
        assert acl.inbound[0].port.start == 20
        assert acl.inbound[0].port.end == 20

    def test_simple_rule_with_port_range(self):
        acl = self.vpc.add_network_acl(
            name='test-acl',
            inbound=[dict(
                network='10.0.0.0/20',
                protocol='tcp',
                port__start=20,
                port__end=40,
            )]
        )
        assert acl.inbound[0].port.start == 20
        assert acl.inbound[0].port.end == 40

    def test_mixing_port_and_port__start(self):
        self.assertRaises(
            errors.InvalidParameter,
            self.vpc.add_network_acl,
            name='test-acl',
            inbound=[dict(
                network='10.0.0.0/20',
                protocol='tcp',
                port=20,
                port__start=20,
            )]
        )

    def test_mixing_port_and_port__end(self):
        self.assertRaises(
            errors.InvalidParameter,
            self.vpc.add_network_acl,
            name='test-acl',
            inbound=[dict(
                network='10.0.0.0/20',
                protocol='tcp',
                port=20,
                port__end=20,
            )]
        )
