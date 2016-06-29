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


class TestAASScalingPolicyCreation(unittest.TestCase):

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
        policy = self.aws.add_scaling_policy(
            name='mytest-policy',
            scalable_target=self.aws.get_scalable_target(
                service='ecs',
                resource='...',
                scalable_dimension='...',
            ),
        )
        target_describer = self.goal.get_service(policy.scalable_target, 'describe')
        applicator = self.goal.get_service(policy, 'apply')

        target_stub = Stubber(target_describer.client)
        target_stub.add_response(
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

        stub = Stubber(applicator.client)
        stub.add_response(
            'describe_scaling_policies',
            service_response={
                'ScalingPolicies': [],
            },
            expected_params={
                'PolicyNames': ['mytest-policy'],
                'ServiceNamespace': 'ecs',
            },
        )
        stub.add_response(
            'put_scaling_policy',
            service_response={
                'PolicyARN': '1234567890abcedfghijklmnopqrstuvwxyz',
            },
            expected_params={
                'PolicyName': 'mytest-policy',
                'PolicyType': 'StepScaling',
                'ServiceNamespace': 'ecs',
                'ResourceId': '...',
                'ScalableDimension': '...',
            },
        )
        stub.add_response(
            'describe_scaling_policies',
            service_response={
                'ScalingPolicies': [{
                    'PolicyName': 'mytest-policy',
                    'PolicyARN': '1234567890abcedfghijklmnopqrstuvwxyz',
                    'ServiceNamespace': '',
                    'ResourceId': '1234567890abcedfghijklmnopqrstuvwxyz',
                    'ScalableDimension': '',
                    'PolicyType': '',
                    'CreationTime': datetime.datetime.now(),
                }],
            },
            expected_params={
                'PolicyNames': ['mytest-policy'],
                'ServiceNamespace': 'ecs',
            },
        )
        stub.add_response(
            'describe_scaling_policies',
            service_response={
                'ScalingPolicies': [{
                    'PolicyName': 'mytest-policy',
                    'PolicyARN': '1234567890abcedfghijklmnopqrstuvwxyz',
                    'ServiceNamespace': '',
                    'ResourceId': '1234567890abcedfghijklmnopqrstuvwxyz',
                    'ScalableDimension': '',
                    'PolicyType': '',
                    'CreationTime': datetime.datetime.now(),
                }],
            },
            expected_params={
                'PolicyNames': ['mytest-policy'],
                'ServiceNamespace': 'ecs',
            },
        )
        stub.add_response(
            'describe_scaling_policies',
            service_response={
                'ScalingPolicies': [{
                    'PolicyName': 'mytest-policy',
                    'PolicyARN': '1234567890abcedfghijklmnopqrstuvwxyz',
                    'ServiceNamespace': '',
                    'ResourceId': '1234567890abcedfghijklmnopqrstuvwxyz',
                    'ScalableDimension': '',
                    'PolicyType': '',
                    'CreationTime': datetime.datetime.now(),
                }],
            },
            expected_params={
                'PolicyNames': ['mytest-policy'],
                'ServiceNamespace': 'ecs',
            },
        )

        with target_stub:
            with stub:
                self.goal.execute()

    def test_update_policy_no_change(self):
        policy = self.aws.add_scaling_policy(
            name='mytest-policy',
            scalable_target=self.aws.get_scalable_target(
                service='ecs',
                resource='...',
                scalable_dimension='...',
            ),
        )
        target_describer = self.goal.get_service(policy.scalable_target, 'describe')
        applicator = self.goal.get_service(policy, 'apply')

        target_stub = Stubber(target_describer.client)
        target_stub.add_response(
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

        stub = Stubber(applicator.client)
        stub.add_response(
            'describe_scaling_policies',
            service_response={
                'ScalingPolicies': [{
                    'PolicyName': 'mytest-policy',
                    'PolicyARN': '1234567890abcedfghijklmnopqrstuvwxyz',
                    'ServiceNamespace': '',
                    'ResourceId': '1234567890abcedfghijklmnopqrstuvwxyz',
                    'ScalableDimension': '',
                    'PolicyType': '',
                    'CreationTime': datetime.datetime.now(),
                }],
            },
            expected_params={
                'PolicyNames': ['mytest-policy'],
                'ServiceNamespace': 'ecs',
            },
        )

        with target_stub:
            with stub:
                self.assertEqual(len(list(self.goal.plan())), 0)
                self.assertEqual(len(self.goal.get_changes(policy)), 0)


class TestAASScalingPolicyDestruction(unittest.TestCase):

    def setUp(self):
        self.workspace = workspace.Workspace()
        self.aws = self.workspace.add_aws(access_key_id='dummy', secret_access_key='dummy', region='eu-west-1')
        self.goal = goals.create(
            'destroy',
            self.workspace,
            frontends.ConsoleFrontend(interactive=False),
            map=SerialMap
        )

    def test_destroy_policy(self):
        policy = self.aws.add_scaling_policy(
            name='mytest-policy',
            scalable_target=self.aws.get_scalable_target(
                service='ecs',
                resource='...',
                scalable_dimension='...',
            ),
        )
        applicator = self.goal.get_service(policy, 'destroy')

        target_describer = self.goal.get_service(policy.scalable_target, 'describe')
        target_stub = Stubber(target_describer.client)
        target_stub.add_response(
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

        stub = Stubber(applicator.client)
        stub.add_response(
            'describe_scaling_policies',
            service_response={
                'ScalingPolicies': [],
            },
            expected_params={
                'PolicyNames': ['mytest-policy'],
                'ServiceNamespace': 'ecs',
            },
        )

        with target_stub:
            with stub:
                self.assertEqual(len(list(self.goal.plan())), 0)
                self.assertEqual(len(self.goal.get_changes(policy)), 0)

    def test_delete_policy(self):
        policy = self.aws.add_scaling_policy(
            name='mytest-policy',
            scalable_target=self.aws.get_scalable_target(
                service='ecs',
                resource='...',
                scalable_dimension='...',
            ),
        )
        applicator = self.goal.get_service(policy, 'destroy')

        target_describer = self.goal.get_service(policy.scalable_target, 'describe')
        target_stub = Stubber(target_describer.client)
        target_stub.add_response(
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

        stub = Stubber(applicator.client)
        stub.add_response(
            'describe_scaling_policies',
            service_response={
                'ScalingPolicies': [{
                    'PolicyName': 'mytest-policy',
                    'PolicyARN': '1234567890abcedfghijklmnopqrstuvwxyz',
                    'ServiceNamespace': '',
                    'ResourceId': '1234567890abcedfghijklmnopqrstuvwxyz',
                    'ScalableDimension': '',
                    'PolicyType': '',
                    'CreationTime': datetime.datetime.now(),
                }],
            },
            expected_params={
                'PolicyNames': ['mytest-policy'],
                'ServiceNamespace': 'ecs',
            },
        )
        stub.add_response(
            'delete_scaling_policy',
            service_response={},
            expected_params={
                'PolicyName': 'mytest-policy',
                'ServiceNamespace': 'ecs',
                'ResourceId': '...',
                'ScalableDimension': '...',
            }
        )

        with target_stub:
            with stub:
                self.goal.execute()
