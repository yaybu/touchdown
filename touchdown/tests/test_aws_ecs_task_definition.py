# Copyright 2016 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the 'License');
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


class TestECSTaskCreation(unittest.TestCase):

    def setUp(self):
        self.workspace = workspace.Workspace()
        self.aws = self.workspace.add_aws(access_key_id='dummy', secret_access_key='dummy', region='eu-west-1')
        self.goal = goals.create(
            'apply',
            self.workspace,
            frontends.ConsoleFrontend(interactive=False),
            map=SerialMap
        )

    def test_create_task_definition(self):
        task_definition = self.aws.add_ecs_task_definition(
            name='mytest-taskdef',
            containers=[{
                'name': 'fred',
                'image': 'ubuntu:14.04',
            }],
        )
        applicator = self.goal.get_service(task_definition, 'apply')

        with Stubber(applicator.client) as stub:
            stub.add_response(
                'describe_task_definition',
                service_response={
                    'taskDefinition': {},
                },
                expected_params={
                    'taskDefinition': 'mytest-taskdef',
                },
            )
            stub.add_response(
                'register_task_definition',
                service_response={
                    'taskDefinition': {
                        'family': 'mytest-taskdef',
                    },
                },
                expected_params={
                    'family': 'mytest-taskdef',
                    'containerDefinitions': [{
                        'name': 'fred',
                        'image': 'ubuntu:14.04',
                        # FIXME: It shouldn't need to send dockerLabels, though this is harmless
                        'dockerLabels': {},
                    }],
                },
            )

            self.goal.execute()

    def test_update_task_definition(self):
        task_definition = self.aws.add_ecs_task_definition(name='mytest-taskdef')
        applicator = self.goal.get_service(task_definition, 'apply')

        with Stubber(applicator.client) as stub:
            stub.add_response(
                'describe_task_definition',
                service_response={
                    'taskDefinition': {
                        'family': 'mytest-taskdef',
                    },
                },
                expected_params={
                    'taskDefinition': 'mytest-taskdef',
                },
            )

            self.assertEqual(len(list(self.goal.plan())), 0)
            self.assertEqual(len(self.goal.get_changes(task_definition)), 0)


class TestECSTaskDestruction(unittest.TestCase):

    def setUp(self):
        self.workspace = workspace.Workspace()
        self.aws = self.workspace.add_aws(access_key_id='dummy', secret_access_key='dummy', region='eu-west-1')
        self.goal = goals.create(
            'destroy',
            self.workspace,
            frontends.ConsoleFrontend(interactive=False),
            map=SerialMap
        )

    def test_destroy_task_definition(self):
        task_definition = self.aws.add_ecs_task_definition(name='mytest-taskdef')
        applicator = self.goal.get_service(task_definition, 'destroy')

        with Stubber(applicator.client) as stub:
            stub.add_response(
                'describe_task_definition',
                service_response={
                    'taskDefinition': {
                        'family': 'mytest-taskdef'
                    },
                },
                expected_params={
                    'taskDefinition': 'mytest-taskdef',
                },
            )
            stub.add_response(
                'deregister_task_definition',
                service_response={
                    'taskDefinition': {
                        'family': 'mytest-taskdef',
                    },
                },
                expected_params={
                    'taskDefinition': 'mytest-taskdef',
                },
            )

            self.goal.execute()

    def test_no_task_definition_to_destroy(self):
        task_definition = self.aws.add_ecs_task_definition(name='mytest-taskdef')
        applicator = self.goal.get_service(task_definition, 'destroy')

        with Stubber(applicator.client) as stub:
            stub.add_response(
                'describe_task_definition',
                service_response={},
                expected_params={
                    'taskDefinition': 'mytest-taskdef',
                },
            )

            self.assertEqual(len(list(self.goal.plan())), 0)
            self.assertEqual(len(self.goal.get_changes(task_definition)), 0)
