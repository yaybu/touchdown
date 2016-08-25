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

import datetime

from botocore.stub import ANY

from .service import ServiceStubber


class HostedZoneStubber(ServiceStubber):

    client_service = 'route53'

    def make_id(self, name):
        return 'Z' + super(HostedZoneStubber, self).make_id(name)[:12].upper()

    def add_list_hosted_zones_empty_response(self):
        return self.add_response(
            'list_hosted_zones',
            service_response={
                'HostedZones': [],
                'Marker': '',
                'IsTruncated': False,
                'MaxItems': '15',
            },
            expected_params={
            },
        )

    def add_list_hosted_zones_one_response(self):
        return self.add_response(
            'list_hosted_zones',
            service_response={
                'HostedZones': [{
                    'Id': self.make_id(self.resource.name),
                    'Name': self.resource.name,
                    'CallerReference': 'CALLER-REFERENCE-HERE',
                }],
                'Marker': '',
                'IsTruncated': False,
                'MaxItems': '15',
            },
            expected_params={
            },
        )

    def add_list_resource_record_sets(self, resource_record_sets=None):
        return self.add_response(
            'list_resource_record_sets',
            service_response={
                'ResourceRecordSets': resource_record_sets or [],
                'IsTruncated': False,
                'MaxItems': '15',
            },
            expected_params={
                'HostedZoneId': self.make_id(self.resource.name),
            },
        )

    def add_create_hosted_zone(self):
        return self.add_response(
            'create_hosted_zone',
            service_response={
                'ChangeInfo': {
                    'Id': '',
                    'SubmittedAt': datetime.datetime.now(),
                    'Status': 'INSYNC',
                },
                'HostedZone': {
                    'Id': self.make_id(self.resource.name),
                    'Name': self.resource.name,
                    'CallerReference': '-',
                },
                'DelegationSet': {
                    'NameServers': [
                        'ns1.example.com',
                    ],
                },
                'Location': '',
            },
            expected_params={
                'Name': self.resource.name.rstrip('.') + '.',
                'CallerReference': ANY,
            }
        )

    def add_change_resource_record_sets_upsert(self, upsert):
        return self.add_change_resource_record_sets('UPSERT', upsert)

    def add_change_resource_record_sets_delete(self, delete):
        return self.add_change_resource_record_sets('DELETE', delete)

    def add_change_resource_record_sets(self, action, change):
        return self.add_response(
            'change_resource_record_sets',
            service_response={
                'ChangeInfo': {
                    'Id': '',
                    'SubmittedAt': datetime.datetime.now(),
                    'Status': 'INSYNC',
                },
            },
            expected_params={
                'ChangeBatch': {
                    'Changes': [{
                        'Action': action,
                        'ResourceRecordSet': change,
                    }],
                },
                'HostedZoneId': self.make_id(self.resource.name),
            }
        )

    def add_delete_hosted_zone(self):
        return self.add_response(
            'delete_hosted_zone',
            service_response={
                'ChangeInfo': {
                    'Id': '',
                    'SubmittedAt': datetime.datetime.now(),
                    'Status': 'INSYNC',
                }
            },
            expected_params={
                'Id': self.make_id(self.resource.name),
            }
        )
