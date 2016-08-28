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


class SecurityGroupStubber(ServiceStubber):

    client_service = 'ec2'

    def make_id(self, name):
        return 'sg-' + super(SecurityGroupStubber, self).make_id(name)[:8]

    def add_describe_security_groups_empty_response(self, vpc_id):
        return self.add_response(
            'describe_security_groups',
            service_response={
                'SecurityGroups': [],
            },
            expected_params={
                'Filters': [
                    {'Name': 'group-name', 'Values': [self.resource.name]},
                    {'Name': 'vpc-id', 'Values': [vpc_id]},
                ],
            },
        )

    def add_describe_security_groups_one_response(self, vpc_id):
        return self.add_response(
            'describe_security_groups',
            service_response={
                'SecurityGroups': [{
                    'GroupName': self.resource.name,
                    'GroupId': self.make_id(self.resource.name),
                }],
            },
            expected_params={
                'Filters': [
                    {'Name': 'group-name', 'Values': [self.resource.name]},
                    {'Name': 'vpc-id', 'Values': [vpc_id]},
                ],
            },
        )

    def add_create_security_group(self, vpc_id):
        return self.add_response(
            'create_security_group',
            service_response={
                'GroupId': self.make_id(self.resource.name),
            },
            expected_params={
                'VpcId': vpc_id,
                'GroupName': self.resource.name,
                'Description': self.resource.description,
            }
        )

    def add_authorize_security_group_ingress(self, ingress):
        return self.add_response(
            'authorize_security_group_ingress',
            service_response={},
            expected_params={
                'GroupId': self.make_id(self.resource.name),
                'IpPermissions': ingress,
            },
        )

    def add_delete_security_group(self):
        return self.add_response(
            'delete_security_group',
            service_response={},
            expected_params={
                'GroupId': self.make_id(self.resource.name),
            },
        )
