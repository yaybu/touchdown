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

import datetime

import mock

from botocore.stub import Stubber

from touchdown.tests.aws import StubberTestCase
from touchdown.tests.stubs.aws import RoleStubber


class TestCreateRole(StubberTestCase):

    def test_create_role(self):
        goal = self.create_goal('apply')

        role = self.fixtures.enter_context(RoleStubber(
            goal.get_service(
                self.aws.add_role(
                    name='my-test-role',
                    assume_role_policy={
                        'Statement': [{
                            'Effect': 'Allow',
                            'Principal': {'Service': 'ec2.amazonaws.com'},
                            'Action': 'sts:AssumeRole',
                        }],
                    },
                ),
                'apply',
            )
        ))

        role.add_list_roles_empty_response_by_name()
        role.add_create_role(
            assume_role_policy_document=(
                '{"Statement": [{"Action": "sts:AssumeRole", "Effect": "Allow", '
                '"Principal": {"Service": "ec2.amazonaws.com"}, "Sid": ""}], '
                '"Version": "2012-10-17"}'
            )
        )

        goal.execute()

    def test_create_role_idempotent(self):
        goal = self.create_goal('apply')

        role = self.fixtures.enter_context(RoleStubber(
            goal.get_service(
                self.aws.add_role(
                    name='my-test-role',
                    assume_role_policy={
                        'Statement': [{
                            'Effect': 'Allow',
                            'Principal': {'Service': 'ec2.amazonaws.com'},
                            'Action': 'sts:AssumeRole',
                        }],
                    },
                ),
                'apply',
            )
        ))

        role.add_list_roles_one_response_by_name(
            assume_role_policy_document=(
                '{"Statement": [{"Action": "sts:AssumeRole", "Effect": "Allow",'
                '"Principal": {"Service": "ec2.amazonaws.com"}, "Sid": ""}],'
                '"Version": "2012-10-17"}'
            )
        )
        role.add_list_role_policies()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(role.resource)), 0)


class TestUpdateRole(StubberTestCase):

    def test_add_policy(self):
        goal = self.create_goal('apply')

        role = self.fixtures.enter_context(RoleStubber(
            goal.get_service(
                self.aws.add_role(
                    name='my-test-role',
                    policies={
                        'logs': {
                            'Version': '2012-10-17',
                            'Statement': [{
                                'Effect': 'Allow',
                                'Action': [
                                    'logs:PutLogEvents',
                                    'logs:CreateLogStream',
                                ],
                                'Resource': '*',
                            }],
                        },
                    },
                ),
                'apply',
            )
        ))

        role.add_list_roles_one_response_by_name()
        role.add_list_role_policies()
        role.add_put_role_policy('logs', (
            '{"Statement": [{"Action": ["logs:PutLogEvents", '
            '"logs:CreateLogStream"], "Effect": "Allow", "Resource": "*"}], '
            '"Version": "2012-10-17"}'
            )
        )
        goal.execute()

    def test_update_policy(self):
        goal = self.create_goal('apply')

        role = self.fixtures.enter_context(RoleStubber(
            goal.get_service(
                self.aws.add_role(
                    name='my-test-role',
                    policies={
                        'logs': {
                            'Version': '2012-10-17',
                            'Statement': [{
                                'Effect': 'Allow',
                                'Action': [
                                    'logs:PutLogEvents',
                                ],
                                'Resource': '*',
                            }],
                        },
                    },
                ),
                'apply',
            )
        ))

        role.add_list_roles_one_response_by_name()
        role.add_list_role_policies('logs')
        role.add_get_role_policy('logs', (
            '{"Version": "2012-10-17", "Statement": [{"Action": ['
            '"logs:PutLogEvents", "logs:CreateLogStream"], '
            '"Resource": "*", "Effect": "Allow"}]}'
        ))
        role.add_put_role_policy('logs', (
            '{"Statement": [{"Action": ["logs:PutLogEvents"], '
            '"Effect": "Allow", "Resource": "*"}], "Version": "2012-10-17"}'
        ))

        goal.execute()

    def test_remove_policy(self):
        goal = self.create_goal('apply')

        role = self.fixtures.enter_context(RoleStubber(
            goal.get_service(
                self.aws.add_role(
                    name='my-test-role',
                    policies={},
                ),
                'apply',
            )
        ))

        role.add_list_roles_one_response_by_name()
        role.add_list_role_policies('logs')
        role.add_delete_role_policy('logs')
        goal.execute()


class TestDestroyRole(StubberTestCase):

    def test_destroy_role(self):
        goal = self.create_goal('destroy')

        role = self.fixtures.enter_context(RoleStubber(
            goal.get_service(
                self.aws.add_role(
                    name='my-test-role',
                    assume_role_policy={
                        'Statement': [{
                            'Effect': 'Allow',
                            'Principal': {'Service': 'ec2.amazonaws.com'},
                            'Action': 'sts:AssumeRole',
                        }],
                    },
                ),
                'destroy',
            )
        ))

        role.add_list_roles_one_response_by_name()
        role.add_list_role_policies()
        role.add_delete_role()
        goal.execute()

    def test_destroy_role_idempotent(self):
        goal = self.create_goal('destroy')

        role = self.fixtures.enter_context(RoleStubber(
            goal.get_service(
                self.aws.add_role(
                    name='my-test-role',
                    assume_role_policy={
                        'Statement': [{
                            'Effect': 'Allow',
                            'Principal': {'Service': 'ec2.amazonaws.com'},
                            'Action': 'sts:AssumeRole',
                        }],
                    },
                ),
                'destroy',
            )
        ))

        role.add_list_roles_empty_response_by_name()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(role.resource)), 0)


class TestGetSigninUrl(StubberTestCase):

    def test_get_signin_url(self):
        goal = self.create_goal('get-signin-url')

        role = self.fixtures.enter_context(RoleStubber(
            goal.get_service(
                self.aws.get_role(name='read-only'),
                'get-signin-url',
            )
        ))

        role.add_list_roles_one_response_by_name()

        stub = self.fixtures.enter_context(Stubber(role.service.sts))
        stub.add_response(
            'assume_role',
            service_response={
                'Credentials': {
                    'AccessKeyId': 'AK12345678901234',
                    'SecretAccessKey': 'AK1234567890',
                    'SessionToken': '01234567890',
                    'Expiration': datetime.datetime.now(),
                }
            },
            expected_params={
                'RoleArn': '12345678901234567890',
                'RoleSessionName': 'touchdown-get-signin-url'
            },
        )

        get = self.fixtures.enter_context(mock.patch('touchdown.aws.iam.role.requests.get'))
        get.return_value.json.return_value = {
            'SigninToken': 'abcdefghijklmnonpqrstuvwxyz',
        }

        echo = self.fixtures.enter_context(mock.patch.object(goal.ui, 'echo'))

        goal.execute('read-only')

        get.assert_called_with(
            'https://signin.aws.amazon.com/federation',
            params={
                'Action': 'getSigninToken',
                'Session': '{"sessionId": "AK12345678901234", "sessionKey": "AK1234567890", "sessionToken": "01234567890"}',
            },
        )

        echo.assert_called_with((
            'https://signin.aws.amazon.com/federation?'
            'Action=login&'
            'Destination=https%3A%2F%2Fconsole.aws.amazon.com%2F&'
            'SigninToken=abcdefghijklmnonpqrstuvwxyz&'
            'Issuer=touchdown'
        ))


class TestGetCredentials(StubberTestCase):

    def test_get_temporary_credentials(self):
        goal = self.create_goal('get-credentials')

        role = self.fixtures.enter_context(RoleStubber(
            goal.get_service(
                self.aws.get_role(name='read-only'),
                'get-credentials',
            )
        ))

        role.add_list_roles_one_response_by_name()

        stub = self.fixtures.enter_context(Stubber(role.service.sts))
        stub.add_response(
            'assume_role',
            service_response={
                'Credentials': {
                    'AccessKeyId': 'AK12345678901234',
                    'SecretAccessKey': 'AK1234567890',
                    'SessionToken': '01234567890',
                    'Expiration': datetime.datetime.now(),
                }
            },
            expected_params={
                'RoleArn': '12345678901234567890',
                'RoleSessionName': 'touchdown-get-credentials'
            },
        )

        echo = self.fixtures.enter_context(mock.patch.object(goal.ui, 'echo'))

        goal.execute('read-only')
        echo.assert_called_with(
            'AWS_ACCESS_KEY_ID=\'AK12345678901234\'; export AWS_ACCESS_KEY_ID;\n'
            'AWS_SECRET_ACCESS_KEY=\'AK1234567890\'; export AWS_SECRET_ACCESS_KEY;\n'
            'AWS_SESSION_TOKEN=\'01234567890\'; export AWS_SESSION_TOKEN;\n'
            'PS1=\'(read-only) $PS1\'; export PS1;\n'
        )
