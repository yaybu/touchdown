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

from touchdown.core.workspace import Workspace
from touchdown.core import errors


class TestNetworkAclRules(unittest.TestCase):

    def setUp(self):
        self.workspace = Workspace()
        self.aws = self.workspace.add_aws(region='eu-west-1')
        self.vpc = self.aws.add_vpc(name='test-vpc')

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
