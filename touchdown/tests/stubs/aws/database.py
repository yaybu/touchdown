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


class DatabaseStubber(ServiceStubber):

    client_service = 'rds'

    def add_describe_db_instances_empty(self):
        return self.add_client_error(
            'describe_db_instances',
            service_error_code='DBInstanceNotFound',
            service_message='',
        )

    def add_describe_db_instances_one(self):
        return self.add_response(
            'describe_db_instances',
            service_response={
                'DBInstances': [{
                    'DBInstanceIdentifier': self.resource.name,
                    'DBInstanceStatus': 'available',
                }],
            },
            expected_params={
                'DBInstanceIdentifier': self.resource.name,
            }
        )

    def add_create_db_instance(self, password='password'):
        return self.add_response(
            'create_db_instance',
            service_response={
                'DBInstance': {
                    'DBInstanceIdentifier': self.resource.name,
                },
            },
            expected_params={
                'DBInstanceIdentifier': self.resource.name,
                'AllocatedStorage': 5,
                'DBInstanceClass': 'db.m3.medium',
                'Engine': 'postgres',
                'MasterUserPassword': password,
                'MasterUsername': 'root',
                'StorageEncrypted': True,
            },
        )

    def add_delete_db_instance(self):
        return self.add_response(
            'delete_db_instance',
            service_response={},
            expected_params={
                'DBInstanceIdentifier': self.resource.name,
                'SkipFinalSnapshot': True,
            },
        )
