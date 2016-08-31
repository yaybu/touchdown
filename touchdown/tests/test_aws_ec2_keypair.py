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

import os
import unittest

from touchdown.aws.ec2.keypair import PublicKeyFromPrivateKey
from touchdown.tests.aws import StubberTestCase
from touchdown.tests.stubs.aws import KeyPairStubber


PUBLIC_KEY_PATH = os.path.join(
    os.path.dirname(__file__),
    'assets/id_rsa_test.pub'
)

PRIVATE_KEY_PATH = os.path.join(
    os.path.dirname(__file__),
    'assets/id_rsa_test'
)

public_key = (
    'ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA6NF8iallvQVp22WDkTkyrtvp9eWW6A8YVr+k'
    'z4TjGYe7gHzIw+niNltGEFHzD8+v1I2YJ6oXevct1YeS0o9HZyN1Q9qgCgzUFtdOKLv6Iedp'
    'lqoPkcmF0aYet2PkEDo3MlTBckFXPITAMzF8dJSIFo9D8HfdOV0IAdx4O7PtixWKn5y2hMNG'
    '0zQPyUecp4pzC6kivAIhyfHilFR61RGL+GPXQ2MWZWFYbAGjyiYJnAmCP3NOTd0jMZEnDkbU'
    'vxhMmBYSdETk1rRgm+R4LOzFUGaHqHDLKLX+FIPKcF96hrucXzcWyLbIbEgE98OHlnVYCzRd'
    'K8jlqm8tehUc9c9WhQ== insecure public key'
    )


class TestCreateKeyPair(StubberTestCase):

    def test_create_keypair(self):
        goal = self.create_goal('apply')

        keypair = self.fixtures.enter_context(KeyPairStubber(
            goal.get_service(
                self.aws.add_keypair(
                    name='test-keypair',
                    public_key=public_key,
                ),
                'apply',
            )
        ))

        keypair.add_describe_keypairs_empty_response_by_name()
        keypair.add_import_key_pair(public_key)
        keypair.add_describe_keypairs_one_response_by_name()
        keypair.add_describe_keypairs_one_response_by_name()

        goal.execute()

    def test_create_keypair_idempotent(self):
        goal = self.create_goal('apply')

        keypair = self.fixtures.enter_context(KeyPairStubber(
            goal.get_service(
                self.aws.add_keypair(
                    name='test-keypair',
                    public_key=public_key,
                ),
                'apply',
            )
        ))

        keypair.add_describe_keypairs_one_response_by_name()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(keypair.resource)), 0)


class TestDestroyKeyPair(StubberTestCase):

    def test_destroy_keypair(self):
        goal = self.create_goal('destroy')

        keypair = self.fixtures.enter_context(KeyPairStubber(
            goal.get_service(
                self.aws.add_keypair(
                    name='test-keypair',
                    public_key=public_key,
                ),
                'destroy',
            )
        ))

        keypair.add_describe_keypairs_one_response_by_name()
        keypair.add_delete_key_pair()

        goal.execute()

    def test_destroy_keypair_idempotent(self):
        goal = self.create_goal('destroy')

        keypair = self.fixtures.enter_context(KeyPairStubber(
            goal.get_service(
                self.aws.add_keypair(
                    name='test-keypair',
                    public_key=public_key,
                ),
                'destroy',
            )
        ))

        keypair.add_describe_keypairs_empty_response_by_name()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(keypair.resource)), 0)


class TestPublicKeyFromPrivateKey(unittest.TestCase):

    def test_serialize_private_key_as_public_key(self):
        with open(PRIVATE_KEY_PATH, 'r') as fp:
            private_key = fp.read()

        s = PublicKeyFromPrivateKey()
        public_key = s.render(None, private_key)

        with open(PUBLIC_KEY_PATH, 'r') as fp:
            assert public_key == fp.read()
