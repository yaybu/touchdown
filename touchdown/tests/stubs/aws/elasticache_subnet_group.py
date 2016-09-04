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


class ElastiCacheSubnetGroupStubber(ServiceStubber):

    client_service = 'rds'

    def add_describe_cache_subnet_groups_empty(self):
        return self.add_response(
            'describe_cache_subnet_groups',
            service_response={
                'CacheSubnetGroups': [],
            },
            expected_params={
                'CacheSubnetGroupName': self.resource.name,
            }
        )

    def add_describe_cache_subnet_groups_one(self):
        return self.add_response(
            'describe_cache_subnet_groups',
            service_response={
                'CacheSubnetGroups': [{
                    'CacheSubnetGroupName': self.resource.name,
                }],
            },
            expected_params={
                'CacheSubnetGroupName': self.resource.name,
            }
        )

    def add_create_subnet_group(self):
        return self.add_response(
            'create_cache_subnet_group',
            service_response={
                'CacheSubnetGroup': {
                    'CacheSubnetGroupName': self.resource.name,
                },
            },
            expected_params={
                'CacheSubnetGroupName': self.resource.name,
                'CacheSubnetGroupDescription': self.resource.description,
                'SubnetIds': ['subnet-52f2381b']
            },
        )

    def add_delete_subnet_group(self):
        return self.add_response(
            'delete_cache_subnet_group',
            service_response={},
            expected_params={
                'CacheSubnetGroupName': self.resource.name
            },
        )
