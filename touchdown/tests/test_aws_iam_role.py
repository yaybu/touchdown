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

from touchdown.core import errors

from . import aws


class TestRole(aws.TestBasicUsage):

    def setUp(self):
        super(TestRole, self).setUp()
        self.base_url = "https://iam.amazonaws.com/"

    def setUpResource(self):
        self.expected_resource_id = 'my-test-role'
        self.resource = self.aws.add_role(
            name='my-test-role',
            assume_role_policy={
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": ["ec2.amazonaws.com"]},
                    "Action": ["sts:AssumeRole"],
                }],
            },
        )

    def test_no_change(self):
        self.responses.add_fixture("POST", self.base_url, self.fixture_found, expires=1)
        self.responses.add_fixture("POST", self.base_url, "aws_role_policies_0")
        self.runner.dot()
        self.assertRaises(errors.NothingChanged, self.runner.apply)
        self.assertEqual(self.plan.resource_id, self.expected_resource_id)

    def test_delete_role_policy(self):
        self.responses.add_fixture("POST", self.base_url, self.fixture_found, expires=1)
        self.responses.add_fixture("POST", self.base_url, "aws_role_policies_1")
        self.runner.dot()
        self.runner.apply()
        self.assertEqual(self.plan.resource_id, self.expected_resource_id)
