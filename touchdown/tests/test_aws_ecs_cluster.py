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


class TestECSClusterCreation(unittest.TestCase):

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
        cluster = self.aws.add_ecs_cluster(name='mytest-cluster')
        applicator = self.goal.get_service(cluster, 'apply')

        with Stubber(applicator.client) as stub:
            stub.add_response(
                'describe_clusters',
                service_response={
                    'clusters': [],
                },
                expected_params={
                    'clusters': ['mytest-cluster'],
                },
            )
            stub.add_response(
                'create_cluster',
                service_response={
                    'cluster': {
                        'clusterName': 'mytest-cluster',
                    },
                },
                expected_params={
                    'clusterName': 'mytest-cluster',
                },
            )

            self.goal.execute()

    def test_update_cluster(self):
        cluster = self.aws.add_ecs_cluster(name='mytest-cluster')
        applicator = self.goal.get_service(cluster, 'apply')

        with Stubber(applicator.client) as stub:
            stub.add_response(
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

            self.assertEqual(len(list(self.goal.plan())), 0)
            self.assertEqual(len(self.goal.get_changes(cluster)), 0)


class TestECSClusterDestruction(unittest.TestCase):

    def setUp(self):
        self.workspace = workspace.Workspace()
        self.aws = self.workspace.add_aws(access_key_id='dummy', secret_access_key='dummy', region='eu-west-1')
        self.goal = goals.create(
            'destroy',
            self.workspace,
            frontends.ConsoleFrontend(interactive=False),
            map=SerialMap
        )

    def test_destroy_cluster(self):
        cluster = self.aws.add_ecs_cluster(name='mytest-cluster')
        applicator = self.goal.get_service(cluster, 'destroy')

        with Stubber(applicator.client) as stub:
            stub.add_response(
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
            stub.add_response(
                'delete_cluster',
                service_response={
                    'cluster': {
                        'clusterName': 'mytest-cluster',
                    },
                },
                expected_params={
                    'cluster': 'mytest-cluster',
                },
            )

            self.goal.execute()

    def test_no_cluster_to_destroy(self):
        cluster = self.aws.add_ecs_cluster(name='mytest-cluster')
        applicator = self.goal.get_service(cluster, 'destroy')

        with Stubber(applicator.client) as stub:
            stub.add_response(
                'describe_clusters',
                service_response={
                    'clusters': [],
                },
                expected_params={
                    'clusters': ['mytest-cluster'],
                },
            )

            self.assertEqual(len(list(self.goal.plan())), 0)
            self.assertEqual(len(self.goal.get_changes(cluster)), 0)
