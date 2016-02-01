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

from . import aws


class TestNetworkAcl(aws.RecordedBotoCoreTest):

    def test_create_and_delete_network_acl(self):
        vpc = self.aws.add_vpc(
            name='test-vpc',
            cidr_block='192.168.0.0/25',
        )
        vpc.add_network_acl(
            name='test-network-acl',
            inbound=[{
                "network": '10.0.0.0/20',
                "protocol": "udp",
                "port": 25,
                "action": "allow",
            }, {
                "network": '10.0.0.0/20',
                "protocol": "tcp",
                "port__start": 8080,
                "port__end": 8090,
            }],
        )
        self.apply()
        self.destroy()

    def test_create_and_update_and_delete_network_acl(self):
        vpc = self.aws.add_vpc(
            name='test-vpc',
            cidr_block='192.168.0.0/25',
        )
        network_acl = vpc.add_network_acl(
            name='test-network-acl',
            inbound=[{
                "network": '10.0.0.0/20',
                "protocol": "udp",
                "port": 25,
                "action": "allow",
            }, {
                "network": '10.0.0.0/20',
                "protocol": "tcp",
                "port__start": 8080,
                "port__end": 8090,
            }],
        )
        self.apply()

        network_acl.outbound = [{
            "network": '10.0.0.0/20',
            "protocol": "icmp",
            "icmp__type": 3,
            "icmp__code": 4,
            "action": "allow",
        }]
        self.apply(assert_idempotent=False)

        self.destroy()


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
