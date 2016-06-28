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

import datetime
import unittest

from botocore.stub import Stubber

from touchdown import frontends
from touchdown.core import goals, workspace
from touchdown.core.map import SerialMap


class TestAASScalableTargetCreation(unittest.TestCase):

    def setUp(self):
        self.workspace = workspace.Workspace()
        self.aws = self.workspace.add_aws(access_key_id='dummy', secret_access_key='dummy', region='eu-west-1')
        self.goal = goals.create(
            'apply',
            self.workspace,
            frontends.ConsoleFrontend(interactive=False),
            map=SerialMap
        )

    def test_create_target(self):
        target = self.aws.add_scalable_target(
            service='ecs',
            resource='...',
            scalable_dimension='...',
        )
        applicator = self.goal.get_service(target, 'apply')

        with Stubber(applicator.client) as stub:
            stub.add_response(
                'describe_scalable_targets',
                service_response={
                    'ScalableTargets': [],
                },
                expected_params={
                    'ServiceNamespace': 'ecs',
                    'ResourceIds': ['...'],
                    'ScalableDimension': '...',
                },
            )
            stub.add_response(
                'register_scalable_target',
                service_response={},
                expected_params={
                    'ServiceNamespace': 'ecs',
                    'ResourceId': '...',
                    'ScalableDimension': '...',
                },
            )
            stub.add_response(
                'describe_scalable_targets',
                service_response={
                    'ScalableTargets': [{
                        'ServiceNamespace': 'ecs',
                        'ResourceId': '...',
                        'ScalableDimension': '...',
                        'MinCapacity': 0,
                        'MaxCapacity': 0,
                        'RoleARN': '123456789012',
                        'CreationTime': datetime.datetime.now(),
                    }],
                },
                expected_params={
                    'ServiceNamespace': 'ecs',
                    'ResourceIds': ['...'],
                    'ScalableDimension': '...',
                },
            )
            stub.add_response(
                'describe_scalable_targets',
                service_response={
                    'ScalableTargets': [{
                        'ServiceNamespace': 'ecs',
                        'ResourceId': '...',
                        'ScalableDimension': '...',
                        'MinCapacity': 0,
                        'MaxCapacity': 0,
                        'RoleARN': '123456789012',
                        'CreationTime': datetime.datetime.now(),
                    }],
                },
                expected_params={
                    'ServiceNamespace': 'ecs',
                    'ResourceIds': ['...'],
                    'ScalableDimension': '...',
                },
            )

            stub.add_response(
                'describe_scalable_targets',
                service_response={
                    'ScalableTargets': [{
                        'ServiceNamespace': 'ecs',
                        'ResourceId': '...',
                        'ScalableDimension': '...',
                        'MinCapacity': 0,
                        'MaxCapacity': 0,
                        'RoleARN': '123456789012',
                        'CreationTime': datetime.datetime.now(),
                    }],
                },
                expected_params={
                    'ServiceNamespace': 'ecs',
                    'ResourceIds': ['...'],
                    'ScalableDimension': '...',
                },
            )

            self.goal.execute()

    def test_update_target_no_changes(self):
        target = self.aws.add_scalable_target(
            service='ecs',
            resource='...',
            scalable_dimension='...',
        )
        applicator = self.goal.get_service(target, 'apply')

        with Stubber(applicator.client) as stub:
            stub.add_response(
                'describe_scalable_targets',
                service_response={
                    'ScalableTargets': [{
                        'ServiceNamespace': 'ecs',
                        'ResourceId': '...',
                        'ScalableDimension': '...',
                        'MinCapacity': 0,
                        'MaxCapacity': 0,
                        'RoleARN': '123456789012',
                        'CreationTime': datetime.datetime.now(),
                    }],
                },
                expected_params={
                    'ServiceNamespace': 'ecs',
                    'ResourceIds': ['...'],
                    'ScalableDimension': '...',
                },
            )

            self.assertEqual(len(list(self.goal.plan())), 0)
            self.assertEqual(len(self.goal.get_changes(target)), 0)


class TestAASScalableTargetDestruction(unittest.TestCase):

    def setUp(self):
        self.workspace = workspace.Workspace()
        self.aws = self.workspace.add_aws(access_key_id='dummy', secret_access_key='dummy', region='eu-west-1')
        self.goal = goals.create(
            'destroy',
            self.workspace,
            frontends.ConsoleFrontend(interactive=False),
            map=SerialMap
        )

    def test_destroy_target(self):
        target = self.aws.add_scalable_target(
            service='ecs',
            resource='...',
            scalable_dimension='...',
        )
        applicator = self.goal.get_service(target, 'destroy')

        with Stubber(applicator.client) as stub:
            stub.add_response(
                'describe_scalable_targets',
                service_response={
                    'ScalableTargets': [{
                        'ServiceNamespace': 'ecs',
                        'ResourceId': '...',
                        'ScalableDimension': '...',
                        'MinCapacity': 0,
                        'MaxCapacity': 0,
                        'RoleARN': '123456789012',
                        'CreationTime': datetime.datetime.now(),
                    }],
                },
                expected_params={
                    'ServiceNamespace': 'ecs',
                    'ResourceIds': ['...'],
                    'ScalableDimension': '...',
                },
            )
            stub.add_response(
                'deregister_scalable_target',
                service_response={},
                expected_params={
                    'ServiceNamespace': 'ecs',
                    'ResourceId': '...',
                    'ScalableDimension': '...',
                },
            )

            self.goal.execute()

    def test_destroy_target_no_changes(self):
        target = self.aws.add_scalable_target(
            service='ecs',
            resource='...',
            scalable_dimension='...',
        )
        applicator = self.goal.get_service(target, 'destroy')

        with Stubber(applicator.client) as stub:
            stub.add_response(
                'describe_scalable_targets',
                service_response={
                    'ScalableTargets': [],
                },
                expected_params={
                    'ServiceNamespace': 'ecs',
                    'ResourceIds': ['...'],
                    'ScalableDimension': '...',
                },
            )

            self.assertEqual(len(list(self.goal.plan())), 0)
            self.assertEqual(len(self.goal.get_changes(target)), 0)
