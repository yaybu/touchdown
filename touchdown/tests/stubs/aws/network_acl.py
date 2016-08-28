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


class NetworkAclStubber(ServiceStubber):

    client_service = 'ec2'

    def make_id(self, name):
        return 'nacl-' + super(NetworkAclStubber, self).make_id(name)[:8]

    def add_describe_network_acls_empty_response_by_name(self):
        return self.add_response(
            'describe_network_acls',
            service_response={
                'NetworkAcls': [],
            },
            expected_params={
                'Filters': [
                    {'Name': 'vpc-id', 'Values': ['vpc-f96b65a5']}
                ]
            },
        )

    def add_describe_network_acls_one_response_by_name(self):
        return self.add_response(
            'describe_network_acls',
            service_response={
                'NetworkAcls': [{
                    'NetworkAclId': self.make_id(self.resource.name),
                    'Tags': [
                        {'Key': 'Name', 'Value': self.resource.name + '.1'}
                    ],
                    'Entries': [],
                    'Associations': [],
                    'IsDefault': False,
                }],
                'ResponseMetadata': {
                    'HTTPStatusCode': 200,
                },
            },
            expected_params={
                'Filters': [
                    {'Name': 'vpc-id', 'Values': ['vpc-f96b65a5']}
                ]
            },
        )

    def add_create_network_acl(self):
        return self.add_response(
            'create_network_acl',
            service_response={
                'NetworkAcl': {
                    'NetworkAclId': self.make_id(self.resource.name),
                },
            },
            expected_params={
                'VpcId': 'vpc-f96b65a5',
            },
        )

    def add_create_tags(self, **tags):
        tag_list = [{'Key': k, 'Value': v} for (k, v) in tags.items()]
        self.add_response(
            'create_tags',
            service_response={
            },
            expected_params={
                'Resources': [self.make_id(self.resource.name)],
                'Tags': tag_list,
            },
        )

    def add_delete_network_acl(self):
        return self.add_response(
            'delete_network_acl',
            service_response={},
            expected_params={
                'NetworkAclId': self.make_id(self.resource.name),
            },
        )
