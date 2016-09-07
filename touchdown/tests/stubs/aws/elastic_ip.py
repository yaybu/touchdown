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


class ElasticIpStubber(ServiceStubber):

    client_service = 'ec2'

    def make_id(self, name):
        return 'eip-' + super(ElasticIpStubber, self).make_id(name)[:8]

    def add_describe_addresses_one_response(self, public_ip):
        return self.add_response(
            'describe_addresses',
            service_response={
                'Addresses': [{
                    'AllocationId': self.make_id(self.resource.name),
                    'PublicIp': '8.8.8.8',
                }]
            },
            expected_params={
                'Filters': [
                    {'Name': 'public-ip', 'Values': [public_ip]}
                ]
            },
        )

    def add_describe_addresses_empty_response(self, public_ip):
        return self.add_response(
            'describe_addresses',
            service_response={
                'Addresses': [],
            },
            expected_params={
                'Filters': [
                    {'Name': 'public-ip', 'Values': [public_ip]}
                ]
            },
        )

    def add_create_elastic_ip(self):
        return self.add_response(
            'create_elastic_ip',
            service_response={
                'ElasticIp': {
                    'AllocationId': self.make_id(self.resource.name),
                    'PublicIp': '8.8.8.8',
                }
            },
            expected_params={
            },
        )

    def add_attach_elastic_ip(self, vpc_id):
        return self.add_response(
            'attach_elastic_ip',
            service_response={},
            expected_params={
                'AllocationId': self.make_id(self.resource.name),
                'VpcId': vpc_id,
            },
        )

    def add_allocate_address(self):
        return self.add_response(
            'allocate_address',
            service_response={
                'AllocationId': self.make_id(self.resource.name),
                'PublicIp': '8.8.8.8',
            },
            expected_params={
                'Domain': 'vpc',
            },
        )

    def add_release_address(self):
        return self.add_response(
            'release_address',
            service_response={
            },
            expected_params={
                'AllocationId': self.make_id(self.resource.name),
            },
        )
