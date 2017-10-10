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


class VpcStubber(ServiceStubber):

    client_service = 'ec2'

    def make_id(self, name):
        return 'vpc-' + super(VpcStubber, self).make_id(name)[:8]

    def add_describe_vpcs_empty_response_by_name(self):
        return self.add_response(
            'describe_vpcs',
            service_response={
                'Vpcs': [],
            },
            expected_params={
                'Filters': [
                    {'Name': 'tag:Name', 'Values': [self.resource.name]}
                ],
            },
        )

    def add_describe_vpcs_one_response_by_name(self, state='available'):
        return self.add_response(
            'describe_vpcs',
            service_response={
                'Vpcs': [{
                    'VpcId': self.make_id(self.resource.name),
                    'State': state,
                }],
            },
            expected_params={
                'Filters': [
                    {'Name': 'tag:Name', 'Values': [self.resource.name]}
                ],
            },
        )

    def add_describe_vpc_attributes(self):
        self.add_response(
            'describe_vpc_attribute',
            service_response={
                'EnableDnsSupport': {
                    'Value': True
                },
                'VpcId': self.make_id(self.resource.name),
            },
            expected_params={
                'VpcId': self.make_id(self.resource.name),
                'Attribute': 'enableDnsSupport',
            },
        )
        return self.add_response(
            'describe_vpc_attribute',
            service_response={
                'EnableDnsHostnames': {
                    'Value': False
                },
                'VpcId': self.make_id(self.resource.name),
            },
            expected_params={
                'VpcId': self.make_id(self.resource.name),
                'Attribute': 'enableDnsHostnames',
            },
        )

    def add_modify_vpc_attributes(self):
        self.add_response(
            'modify_vpc_attribute',
            service_response={
                'ResponseMetadata': {
                    '...': '...',
                },
            },
            expected_params={
                'VpcId': self.make_id(self.resource.name),
                'EnableDnsSupport': {
                    'Value': False
                }
            },
        )
        return self.add_response(
            'modify_vpc_attribute',
            service_response={
                'ResponseMetadata': {
                    '...': '...',
                },
            },
            expected_params={
                'VpcId': self.make_id(self.resource.name),
                'EnableDnsHostnames': {
                    'Value': True
                }
            },
        )

    def add_create_vpc(self):
        return self.add_response(
            'create_vpc',
            service_response={
                'Vpc': {
                    'VpcId': self.make_id(self.resource.name),
                    'State': 'pending',
                },
            },
            expected_params={
                'CidrBlock': '192.168.0.0/25',
                'InstanceTenancy': 'default',
            },
        )

    def add_create_tags(self, **tags):
        tag_list = [{'Key': k, 'Value': v} for (k, v) in tags.items()]
        return self.add_response(
            'create_tags',
            service_response={
            },
            expected_params={
                'Resources': [self.make_id(self.resource.name)],
                'Tags': tag_list,
            },
        )

    def add_delete_vpc(self):
        return self.add_response(
            'delete_vpc',
            service_response={
            },
            expected_params={
                'VpcId': self.make_id(self.resource.name),
            },
        )
