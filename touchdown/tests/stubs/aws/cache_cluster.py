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

from .service import ServiceStubber


class CacheClusterStubber(ServiceStubber):

    client_service = 'elasticache'

    def add_describe_cache_clusters_empty_response(self):
        return self.add_client_error(
            'describe_cache_clusters',
            service_error_code='CacheClusterNotFound',
            service_message='',
            # expected_params={
            #    'CacheClusterId': self.resource.name,
            # },
        )

    def add_describe_cache_clusters_one_response(self, status='available'):
        return self.add_response(
            'describe_cache_clusters',
            service_response={
                'CacheClusters': [{
                    'CacheClusterId': self.resource.name,
                    'CacheClusterStatus': status,
                    'CacheNodes': [{
                        'Endpoint': {
                            'Address': 'mycacheclu.q68zge.ng.0001.use1devo.elmo-dev.amazonaws.com',
                            'Port': 6379,
                        }
                    }]
                }],
            },
            expected_params={
                'CacheClusterId': self.resource.name,
            }
        )

    def add_create_cache_cluster(self):
        return self.add_response(
            'create_cache_cluster',
            service_response={
                'CacheCluster': {
                    'CacheClusterId': self.resource.name,
                },
            },
            expected_params={
                'CacheClusterId': self.resource.name,
                'CacheNodeType': 'cache.m3.medium',
                'NumCacheNodes': 1,
            },
        )

    def add_delete_cache_cluster(self):
        return self.add_response(
            'delete_cache_cluster',
            service_response={},
            expected_params={
                'CacheClusterId': self.resource.name,
            },
        )
