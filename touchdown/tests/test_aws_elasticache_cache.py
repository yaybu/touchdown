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

from touchdown.tests.aws import StubberTestCase
from touchdown.tests.stubs.aws import (
    CacheClusterStubber,
    LaunchConfigurationStubber,
)


class TestCacheClusterCreation(StubberTestCase):

    def test_create_cache_cluster(self):
        goal = self.create_goal('apply')

        cache_cluster = self.fixtures.enter_context(CacheClusterStubber(
            goal.get_service(
                self.aws.add_cache_cluster(
                    name='my-cache-cluster',
                    instance_class='cache.m3.medium',
                ),
                'apply',
            )
        ))
        cache_cluster.add_describe_cache_clusters_empty_response()
        cache_cluster.add_create_cache_cluster()
        cache_cluster.add_describe_cache_clusters_one_response(status='creating')
        cache_cluster.add_describe_cache_clusters_one_response()
        cache_cluster.add_describe_cache_clusters_one_response()

        goal.execute()

    def test_create_cache_cluster_idempotent(self):
        goal = self.create_goal('apply')

        cache_cluster = self.fixtures.enter_context(CacheClusterStubber(
            goal.get_service(
                self.aws.add_cache_cluster(
                    name='my-cache-cluster',
                    instance_class='cache.m3.medium',
                ),
                'apply',
            )
        ))
        cache_cluster.add_describe_cache_clusters_one_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(cache_cluster.resource)), 0)


class TestCacheClusterDeletion(StubberTestCase):

    def test_delete_cache_cluster(self):
        goal = self.create_goal('destroy')

        cache_cluster = self.fixtures.enter_context(CacheClusterStubber(
            goal.get_service(
                self.aws.add_cache_cluster(
                    name='my-cache-cluster',
                    instance_class='cache.m3.medium',
                ),
                'destroy',
            )
        ))
        cache_cluster.add_describe_cache_clusters_one_response()
        cache_cluster.add_delete_cache_cluster()

        # Wait for it to go away
        cache_cluster.add_describe_cache_clusters_one_response()
        cache_cluster.add_describe_cache_clusters_empty_response()

        goal.execute()

    def test_delete_cache_cluster_idempotent(self):
        goal = self.create_goal('destroy')

        cache_cluster = self.fixtures.enter_context(CacheClusterStubber(
            goal.get_service(
                self.aws.add_cache_cluster(
                    name='my-cache-cluster',
                    instance_class='cache.m3.medium',
                ),
                'destroy',
            )
        ))
        cache_cluster.add_describe_cache_clusters_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(cache_cluster.resource)), 0)


class TestCacheClusterComplications(StubberTestCase):

    def test_with_launch_configuration(self):
        goal = self.create_goal('apply')

        cache_cluster = self.fixtures.enter_context(CacheClusterStubber(
            goal.get_service(
                self.aws.add_cache_cluster(
                    name='my-cache-cluster',
                    instance_class='cache.m3.medium',
                ),
                'apply',
            )
        ))
        cache_cluster.add_describe_cache_clusters_empty_response()
        cache_cluster.add_create_cache_cluster()
        cache_cluster.add_describe_cache_clusters_one_response(status='creating')
        cache_cluster.add_describe_cache_clusters_one_response()
        cache_cluster.add_describe_cache_clusters_one_response()

        launch_config = self.fixtures.enter_context(LaunchConfigurationStubber(
            goal.get_service(
                self.aws.add_launch_configuration(
                    name='my-test-lc',
                    image='ami-cba130bc',
                    instance_type='t2.micro',
                    json_user_data={
                        'REDIS_ADDRESS': cache_cluster.resource.endpoint_address,
                        'REDIS_PORT': cache_cluster.resource.endpoint_port,
                    }
                ),
                'apply',
            )
        ))

        user_data = (
            '{"REDIS_ADDRESS": "mycacheclu.q68zge.ng.0001.use1devo.elmo-dev.amazonaws.com", '
            '"REDIS_PORT": 6379}'
        )

        launch_config.add_describe_launch_configurations_empty_response()
        launch_config.add_describe_launch_configurations_empty_response()
        launch_config.add_create_launch_configuration(user_data=user_data)
        launch_config.add_describe_launch_configurations_one_response(user_data=user_data)
        launch_config.add_describe_launch_configurations_one_response(user_data=user_data)
        launch_config.add_describe_launch_configurations_one_response(user_data=user_data)

        goal.execute()
