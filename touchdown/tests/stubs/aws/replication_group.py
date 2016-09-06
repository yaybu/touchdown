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


class ReplicationGroupStubber(ServiceStubber):

    client_service = 'elasticache'

    def add_describe_replication_groups_empty_response(self):
        return self.add_client_error(
            'describe_replication_groups',
            service_error_code='ReplicationGroupNotFoundFault',
            service_message='',
            # expected_params={
            #    'ReplicationGroupId': self.resource.name,
            # },
        )

    def add_describe_replication_groups_one_response(self, status='available'):
        return self.add_response(
            'describe_replication_groups',
            service_response={
                'ReplicationGroups': [{
                    'ReplicationGroupId': self.resource.name,
                    'Status': status,
                    'NodeGroups': [{
                        'PrimaryEndpoint': {
                            'Address': 'myreplgrp.q68zge.ng.0001.use1devo.elmo-dev.amazonaws.com',
                            'Port': 6379,
                        }
                    }]
                }],
            },
            expected_params={
                'ReplicationGroupId': self.resource.name,
            }
        )

    def add_create_replication_group(self):
        return self.add_response(
            'create_replication_group',
            service_response={
                'ReplicationGroup': {
                    'ReplicationGroupId': self.resource.name,
                },
            },
            expected_params={
                'ReplicationGroupId': self.resource.name,
                'ReplicationGroupDescription': self.resource.name,
            },
        )

    def add_delete_replication_group(self):
        return self.add_response(
            'delete_replication_group',
            service_response={},
            expected_params={
                'ReplicationGroupId': self.resource.name,
                'RetainPrimaryCluster': False
            },
        )
