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
from touchdown.tests.fixtures.aws import VpcFixture
from touchdown.tests.stubs.aws import SecurityGroupStubber


class TestSecurityGroupCreation(StubberTestCase):

    def test_create_security_group(self):
        goal = self.create_goal('apply')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        security_group = self.fixtures.enter_context(SecurityGroupStubber(
            goal.get_service(
                vpcf.vpc.add_security_group(
                    name='test-security-group',
                    description='test-security-group',
                ),
                'apply',
            )
        ))

        security_group.add_describe_security_groups_empty_response('vpc-f96b65a5')
        security_group.add_create_security_group('vpc-f96b65a5')
        security_group.add_describe_security_groups_one_response('vpc-f96b65a5')
        security_group.add_describe_security_groups_one_response('vpc-f96b65a5')

        goal.execute()

    def test_adding_ingress(self):
        goal = self.create_goal('apply')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        security_group = self.fixtures.enter_context(SecurityGroupStubber(
            goal.get_service(
                vpcf.vpc.add_security_group(
                    name='test-security-group',
                    description='test-security-group',
                    ingress=[
                        {'port': 80, 'network': '0.0.0.0/0'},
                    ]
                ),
                'apply',
            )
        ))

        security_group.add_describe_security_groups_empty_response('vpc-f96b65a5')

        security_group.add_create_security_group('vpc-f96b65a5')

        security_group.add_describe_security_groups_one_response('vpc-f96b65a5')
        security_group.add_describe_security_groups_one_response('vpc-f96b65a5')

        security_group.add_authorize_security_group_ingress([{
            'FromPort': 80,
            'ToPort': 80,
            'IpProtocol': 'tcp',
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}],
        }])

        goal.execute()

    def test_create_security_group_idempotent(self):
        goal = self.create_goal('apply')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        security_group = self.fixtures.enter_context(SecurityGroupStubber(
            goal.get_service(
                vpcf.vpc.add_security_group(
                    name='test-security-group',
                    description='test-security-group',
                ),
                'apply',
            )
        ))

        security_group.add_describe_security_groups_one_response('vpc-f96b65a5')

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(security_group.resource)), 0)


class TestSecurityGroupDestroy(StubberTestCase):

    def test_destroy_security_group(self):
        goal = self.create_goal('destroy')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        security_group = self.fixtures.enter_context(SecurityGroupStubber(
            goal.get_service(
                vpcf.vpc.add_security_group(
                    name='test-security-group',
                    description='test-security-group',
                ),
                'destroy',
            )
        ))

        security_group.add_describe_security_groups_one_response('vpc-f96b65a5')
        security_group.add_delete_security_group()

        goal.execute()

    def test_destroy_security_group_idempotent(self):
        goal = self.create_goal('destroy')
        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        security_group = self.fixtures.enter_context(SecurityGroupStubber(
            goal.get_service(
                vpcf.vpc.add_security_group(
                    name='test-security-group',
                    description='test-security-group',
                ),
                'destroy',
            )
        ))

        security_group.add_describe_security_groups_empty_response('vpc-f96b65a5')

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(security_group.resource)), 0)
