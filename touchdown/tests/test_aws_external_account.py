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

from touchdown.tests.aws import StubberTestCase
from touchdown.tests.fixtures.aws import VpcFixture
from touchdown.tests.stubs.aws import ExternalAccountStubber


class TestExternalAccount(StubberTestCase):

    def test_acquire_role(self):
        goal = self.create_goal('apply')

        external_account = self.fixtures.enter_context(ExternalAccountStubber(
            goal.get_service(
                self.aws.add_external_role(
                    name='session-name',
                    arn='arn:aws:iam::123456789012:role/S3Access',
                ),
                'null',
            ),
        ))
        external_account.add_assume_role()

        self.assertEqual(
            external_account.service.session.access_key_id,
            'AKIASSUMEROLEASSUMEROLE',
        )
        self.assertEqual(
            external_account.service.session.secret_access_key,
            'abcdefghijklmnopqrstuvwxyz',
        )
        self.assertEqual(
            external_account.service.session.session_token,
            'zyxwvutsrqpnomlkjihgfedcba',
        )

        vpcf = self.fixtures.enter_context(VpcFixture(
            goal,
            external_account.resource,
        ))
        self.assertEqual(goal.get_service(vpcf.vpc, 'describe').describe_object(), {
            'VpcId': vpcf.vpc_id,
            'EnableDnsHostnames': {'Value': False},
            'EnableDnsSupport': {'Value': True},
            'State': 'available',
        })
