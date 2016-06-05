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

from botocore.stub import Stubber

from touchdown import frontends
from touchdown.core import goals, workspace
from touchdown.core.map import SerialMap


class TestWafRule(unittest.TestCase):

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
        rule = self.aws.add_rule(name="myrule")
        desc = self.goal.get_service(rule, "describe")

        stub = Stubber(desc.client)

        stub.add_response(
            'get_rule',
            {'Rule': {
                'RuleId': 'ZzZzZz',
                'Predicates': [],
            }},
            {'RuleId': 'ZzZzZz'},
        )

        with stub:
            obj = desc.annotate_object({
                "RuleId": "ZzZzZz"
            })

        self.assertEqual(obj["RuleId"], "ZzZzZz")

    def test_delete_rule(self):
        rule = self.aws.add_rule(name="myrule")

        dest = self.goal.get_service(rule, "destroy")
        dest.object = {
            "Predicates": [{
                "Foo": 1,
            }],
        }

        stub = Stubber(dest.client)
        with stub:
            plan = list(dest.destroy_object())

        self.assertEqual(len(plan), 2)
