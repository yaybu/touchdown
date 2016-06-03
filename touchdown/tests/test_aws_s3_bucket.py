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

import unittest
import mock

from botocore.stub import Stubber

from touchdown import frontends
from touchdown.core import goals, workspace
from touchdown.core.errors import InvalidParameter
from touchdown.core.map import SerialMap

from . import aws


class TestBucketDescribe(unittest.TestCase):

    def setUp(self):
        self.workspace = workspace.Workspace()
        self.aws = self.workspace.add_aws(access_key_id='dummy', secret_access_key='dummy', region='eu-west-1')
        self.goal = goals.create(
            "apply",
            self.workspace,
            frontends.ConsoleFrontend(interactive=False),
            map=SerialMap
        )

    def test_annotate_object(self):
        bucket = self.aws.add_bucket(name="mybucket")
        desc = self.goal.get_service(bucket, "describe")

        desc.client.meta.events.unregister("after-call.s3.GetBucketLocation")

        stub = Stubber(desc.client)

        # See https://github.com/boto/botocore/pull/937
        desc.client.get_bucket_location = mock.Mock(return_value={"LocationConstraint": "eu-central-1"})
        # stub.add_response(
        #     'get_bucket_location',
        #     {'LocationConstraint': 'eu-central-1'},
        #     {'Bucket': 'mybucket'},
        # )
        stub.add_response(
            'get_bucket_cors',
            {'CORSRules': []},
            {'Bucket': 'mybucket'},
        )
        stub.add_response(
            'get_bucket_policy',
            {'Policy': '{}'},
            {'Bucket': 'mybucket'},
        )
        stub.add_response(
            'get_bucket_notification_configuration',
            {},
            {'Bucket': 'mybucket'},
        )
        stub.add_response(
            'get_bucket_accelerate_configuration',
            {},
            {'Bucket': 'mybucket'},
        )

        with stub:
            obj = desc.annotate_object({
                "Name": "ZzZzZz"
            })

        # Assert name isn't trodden on by annotate_object
        self.assertEqual(obj["Name"], "ZzZzZz")


class TestBucketValidation(aws.RecordedBotoCoreTest):

    def test_starts_with_period(self):
        self.assertRaises(InvalidParameter, self.aws.add_bucket, name=".foo")

    def test_ends_with_period(self):
        self.assertRaises(InvalidParameter, self.aws.add_bucket, name="foo.")

    def test_double_period(self):
        self.assertRaises(InvalidParameter, self.aws.add_bucket, name="foo..bar")

    def test_starts_with_hyphen(self):
        self.assertRaises(InvalidParameter, self.aws.add_bucket, name="-foo")

    def test_ends_with_hyphen(self):
        self.assertRaises(InvalidParameter, self.aws.add_bucket, name="foo-")

    def test_hyphen(self):
        self.aws.add_bucket(name="foo--bar")

    def test_upper(self):
        self.assertRaises(InvalidParameter, self.aws.add_bucket, name="FOO")
