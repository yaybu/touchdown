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
from touchdown.tests.stubs.aws import AccountStubber


class TestAccount(StubberTestCase):

    def test_mfa(self):
        goal = self.create_goal('apply')

        self.aws.mfa_serial = 'mymfaserial'
        goal.ui.preseed('mymfaserial', '123456')

        account = self.fixtures.enter_context(AccountStubber(
            goal.get_service(self.aws, 'null')
        ))
        account.add_get_session_token()

        self.assertEqual(
            account.service.session.access_key_id,
            'AKIMFAGETSESSIONMFAGETSESSION',
        )
        self.assertEqual(
            account.service.session.secret_access_key,
            'abcdefghijklmnopqrstuvwxyzmfa',
        )
        self.assertEqual(
            account.service.session.session_token,
            'zyxwvutsrqpnomlkjihgfedcbamfa',
        )

        vpcf = self.fixtures.enter_context(VpcFixture(
            goal,
            account.resource,
        ))
        self.assertEqual(goal.get_service(vpcf.vpc, 'describe').describe_object(), {
            'VpcId': vpcf.vpc_id,
            'EnableDnsHostnames': {'Value': False},
            'EnableDnsSupport': {'Value': True},
            'State': 'available',
        })
