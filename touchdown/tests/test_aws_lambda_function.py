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

import datetime
import os
import shutil
import sys
import tempfile
import unittest

import pytest
from botocore.stub import ANY, Stubber

from touchdown import frontends
from touchdown.core import goals, workspace
from touchdown.core.map import SerialMap


def dummy_function(a, b):
    """ This is a dummy function to test the serializers """
    pass


class TestLambdaFunction(unittest.TestCase):

    def setUp(self):
        self.workspace = workspace.Workspace()
        self.aws = self.workspace.add_aws(access_key_id='dummy', secret_access_key='dummy', region='eu-west-1')
        self.goal = goals.create(
            "apply",
            self.workspace,
            frontends.ConsoleFrontend(interactive=False),
            map=SerialMap
        )

    def test_get_all_unaliased_versions(self):
        self.fn = self.aws.add_lambda_function(
            name="myfunction",
            role=self.aws.get_role(name="myrole"),
            handler="mymodule.myfunction",
            code=dummy_function,
        )
        apply_service = self.goal.get_service(self.fn, "apply")

        with Stubber(apply_service.client) as stub:
            stub.add_response(
                'list_versions_by_function',
                service_response={
                    'Versions': [
                        {
                            'FunctionName': 'myfunction',
                            'Version': '$LATEST',
                        },
                        {
                            'FunctionName': 'myfunction',
                            'Version': '1',
                        },
                        {
                            'FunctionName': 'myfunction',
                            'Version': '2',
                        },
                        {
                            'FunctionName': 'myfunction',
                            'Version': '3',
                        },
                    ],
                },
                expected_params={
                    'FunctionName': 'myfunction'
                },
            )
            stub.add_response(
                'list_aliases',
                service_response={
                    'Aliases': [
                        {
                            'Name': 'stable',
                            'FunctionVersion': '1',
                        }
                    ]
                },
                expected_params={
                    'FunctionName': 'myfunction'
                },
            )
            versions = apply_service.get_all_unaliased_versions()

        self.assertEqual(versions, [{
            "FunctionName": "myfunction",
            "Version": "2",
        }])

    def test_dont_update_code(self):
        self.fn = self.aws.add_lambda_function(
            name="myfunction",
            role=self.aws.get_role(name="myrole"),
            handler="mymodule.myfunction",
            code=dummy_function,
        )
        self.apply_service = self.goal.get_service(self.fn, "apply")
        self.apply_service.object = {
            "FunctionName": "myfunction",
            "CodeSha256": "QWfDvEHUTP0EFEWOjRkXeP733yzB67f9ViAssuXF6/8="
        }

        # FIXME: Zip's produced on Windows have stables hashes (zipping the
        # same thing repeatedly yields the same result)
        # But the hashes are different from posix zips.
        if sys.platform == "win32":
            self.apply_service.object['CodeSha256'] = 'kI3Czz0As/qAcnAq0JzbVG/NzSPUS4khRcbHuKivW0k='

        with Stubber(self.apply_service.client):
            for action in self.apply_service.update_code_by_zip():
                action.run()

    def test_update_code(self):
        self.fn = self.aws.add_lambda_function(
            name="myfunction",
            role=self.aws.get_role(name="myrole"),
            handler="mymodule.myfunction",
            code=dummy_function,
        )
        self.apply_service = self.goal.get_service(self.fn, "apply")
        self.apply_service.object = {
            "FunctionName": "myfunction",
            "CodeSha256": ""
        }
        with Stubber(self.apply_service.client) as stub:
            stub.add_response(
                'update_function_code',
                service_response={
                    'FunctionName': 'myfunction',
                },
                expected_params={
                    'FunctionName': 'myfunction',
                    'ZipFile': ANY,
                    'Publish': True,
                },
            )
            for action in self.apply_service.update_code_by_zip():
                action.run()

    def test_update_code_via_s3(self):
        self.fn = self.aws.add_lambda_function(
            name="myfunction",
            role=self.aws.get_role(name="myrole"),
            handler="mymodule.myfunction",
            s3_file=self.aws.get_bucket(name="mybucket").get_file(name="myfile"),
        )
        self.apply_service = self.goal.get_service(self.fn, "apply")
        self.apply_service.object = {
            "FunctionName": "myfunction",
        }
        with Stubber(self.apply_service.client) as stub:
            stub.add_response(
                'update_function_code',
                service_response={
                    'FunctionName': 'myfunction',
                },
                expected_params={
                    'FunctionName': 'myfunction',
                    'S3Bucket': 'mybucket',
                    'S3Key': 'myfile',
                    'Publish': True,
                },
            )
            for action in self.apply_service.update_code_by_s3():
                action.run()


@pytest.mark.skipif(sys.platform == 'win32', reason="does not run on windows")
class TestLambdaFunctionIntegration(unittest.TestCase):

    def setUp(self):
        self.workspace = workspace.Workspace()
        self.aws = self.workspace.add_aws(access_key_id='dummy', secret_access_key='dummy', region='eu-west-1')
        self.goal = goals.create(
            "apply",
            self.workspace,
            frontends.ConsoleFrontend(interactive=False),
            map=SerialMap
        )
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_build_a_zip(self):
        bundle = self.workspace.add_fuselage_bundle(
            target=self.workspace.add_local()
        )
        bundle.add_execute(command="zip {} {}".format(
            os.path.join(self.test_dir, "lambda.zip"),
            __file__,
        ))
        self.fn = self.aws.add_lambda_function(
            name="myfunction",
            role=self.aws.get_role(name="myrole"),
            handler="mymodule.myfunction",
            code=bundle.add_output(name=os.path.join(self.test_dir, "lambda.zip")),
        )

        role_service = self.goal.get_service(self.fn.role, "describe")
        fn_service = self.goal.get_service(self.fn, "apply")

        role_stubber = Stubber(role_service.client)
        role_stubber.add_response(
            'list_roles',
            service_response={
                'Roles': [{
                    'RoleName': 'myrole',
                    'Path': '/iam/myrole',
                    'RoleId': '1234567890123456',
                    'Arn': '12345678901234567890',
                    'CreateDate': datetime.datetime.now(),
                }],
            },
            expected_params={},
        )

        fn_stubber = Stubber(fn_service.client)
        fn_stubber.add_response(
            'get_function_configuration',
            service_response={
                'FunctionName': 'myfunction',
                'CodeSha256': '',
                'Handler': 'mymodule.myfunction',
                'Role': '12345678901234567890',
            },
            expected_params={
                'FunctionName': 'myfunction',
            },
        )
        fn_stubber.add_response(
            'list_versions_by_function',
            service_response={
                'Versions': [],
            },
            expected_params={
                'FunctionName': 'myfunction',
            },
        )
        fn_stubber.add_response(
            'list_aliases',
            service_response={
                'Aliases': [],
            },
            expected_params={
                'FunctionName': 'myfunction',
            },
        )
        fn_stubber.add_response(
            'update_function_code',
            service_response={
                'FunctionName': 'myfunction',
            },
            expected_params={
                'FunctionName': 'myfunction',
                'ZipFile': ANY,
                'Publish': True,
            },
        )

        with role_stubber:
            with fn_stubber:
                self.goal.execute()
