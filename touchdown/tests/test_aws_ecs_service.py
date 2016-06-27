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


class TestECSServiceCreation(unittest.TestCase):

    def setUp(self):
        self.workspace = workspace.Workspace()
        self.aws = self.workspace.add_aws(access_key_id='dummy', secret_access_key='dummy', region='eu-west-1')
        self.goal = goals.create(
            'apply',
            self.workspace,
            frontends.ConsoleFrontend(interactive=False),
            map=SerialMap
        )

    def test_create_cluster(self):
        cluster = self.aws.get_ecs_cluster(name='mytest-cluster')
        cluster_describer = self.goal.get_service(cluster, 'describe')
        service = cluster.add_service(
            name='mytest-service',
            desired=1,
            task=self.aws.get_ecs_task_definition(name='mytask-definiton'),
        )
        taskdef_describer = self.goal.get_service(service.task, 'describe')
        applicator = self.goal.get_service(service, 'apply')

        cluster_stub = Stubber(cluster_describer.client)
        cluster_stub.add_response(
            'describe_clusters',
            service_response={
                'clusters': [{
                    'clusterName': 'mytest-cluster',
                }],
            },
            expected_params={
                'clusters': ['mytest-cluster'],
            },
        )

        taskdef_stub = Stubber(taskdef_describer.client)
        taskdef_stub.add_response(
            'describe_task_definition',
            service_response={
                'taskDefinition': {
                    'family': 'mytask-definiton',
                },
            },
            expected_params={
                'taskDefinition': 'mytask-definiton',
            },
        )

        applicator_stub = Stubber(applicator.client)
        applicator_stub.add_response(
            'describe_services',
            service_response={
                'services': [],
            },
            expected_params={
                'cluster': 'mytest-cluster',
                'services': ['mytest-service'],
            },
        )
        applicator_stub.add_response(
            'create_service',
            service_response={
                'service': {
                    'serviceName': 'mytest-service',
                },
            },
            expected_params={
                'serviceName': 'mytest-service',
                'cluster': 'mytest-cluster',
                'taskDefinition': 'mytask-definiton',
                'desiredCount': 1,
            },
        )

        with taskdef_stub:
            with cluster_stub:
                with applicator_stub:
                    self.goal.execute()
