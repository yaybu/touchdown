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


class TestGetCredentials(unittest.TestCase):

    def setUp(self):
        self.workspace = workspace.Workspace()
        self.aws = self.workspace.add_aws(access_key_id='dummy', secret_access_key='dummy', region='eu-west-1')
        self.goal = goals.create(
            "get-credentials",
            self.workspace,
            frontends.ConsoleFrontend(interactive=False),
            map=SerialMap
        )

    def test_get_temporary_credentials(self):
        role = self.aws.get_role(name="read-only")
        cred_service = self.goal.get_service(role, "get-credentials")

        with Stubber(cred_service.client) as stub:
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
            with Stubber(cred_service.sts) as stub:
                stub.add_response(
                    'assume_role',
                    service_response={
                        "Credentials": {
                            "AccessKeyId": "AK12345678901234",
                            "SecretAccessKey": "AK1234567890",
                            "SessionToken": "01234567890",
                            "Expiration": datetime.datetime.now(),
                        }
                    },
                    expected_params={
                        'RoleArn': '12345678901234567890',
                        'RoleSessionName': 'touchdown-get-credentials'
                    },
                )
                with mock.patch.object(self.goal.ui, "echo") as m:
                    self.goal.execute("read-only")
                    m.assert_called_with(
                        'AWS_ACCESS_KEY_ID=\'AK12345678901234\'; export AWS_ACCESS_KEY_ID;\n'
                        'AWS_SECRET_ACCESS_KEY=\'AK1234567890\'; export AWS_SECRET_ACCESS_KEY;\n'
                        'AWS_SESSION_TOKEN=\'01234567890\'; export AWS_SESSION_TOKEN;\n'
                        'PS1="(read-only) $PS1"; export PS1;\n'
                    )


class TestRole(aws.RecordedBotoCoreTest):

    def test_create_and_delete_role(self):
        self.aws.add_role(
            name="my-test-role",
            assume_role_policy={
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": "ec2.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }],
            },
        )
        self.apply()
        self.destroy()
