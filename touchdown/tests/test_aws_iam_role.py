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
import unittest

import mock
from botocore.stub import Stubber

from touchdown import frontends
from touchdown.core import goals, workspace
from touchdown.core.map import SerialMap

from . import aws


class TestGetCredentials(aws.StubberTestCase):

    def test_get_temporary_credentials(self):
        goal = self.create_goal('get-credentials')

        role = self.aws.get_role(name='read-only')
        cred_service = goal.get_service(role, 'get-credentials')

        stub = self.fixtures.enter_context(Stubber(cred_service.client))
        stub.add_response(
            'list_roles',
            service_response={
                'Roles': [
                    {
                        'RoleName': 'read-only',
                        'Path': '/iam/myrole',
                        'RoleId': '1234567890123456',
                        'Arn': '12345678901234567890',
                        'CreateDate': datetime.datetime.now(),
                    }
                ]
            },
            expected_params={},
        )

        stub = self.fixtures.enter_context(Stubber(cred_service.sts))
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
            'PS1="(read-only) $PS1"; export PS1;\n'
        )


class TestRole(aws.RecordedBotoCoreTest):

    def test_create_and_delete_role(self):
        self.aws.add_role(
            name='my-test-role',
            assume_role_policy={
                'Statement': [{
                    'Effect': 'Allow',
                    'Principal': {'Service': 'ec2.amazonaws.com'},
                    'Action': 'sts:AssumeRole',
                }],
            },
        )
        self.apply()
        self.destroy()
