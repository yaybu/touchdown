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


class CustomerGatewayStubber(ServiceStubber):

    client_service = 'ec2'

    def make_id(self, name):
        return 'cgw-' + super(CustomerGatewayStubber, self).make_id(name)[:8]

    def add_describe_customer_gateways_empty_response(self):
        return self.add_response(
            'describe_customer_gateways',
            service_response={},
            expected_params={
                'Filters': [
                    {'Name': 'tag:Name', 'Values': [self.resource.name]},
                ],
            },
        )

    def add_describe_customer_gateways_one_response(self, state='available'):
        return self.add_response(
            'describe_customer_gateways',
            service_response={
                'CustomerGateways': [{
                    'CustomerGatewayId': self.make_id(self.resource.name),
                    'State': state,
                }]
            },
            expected_params={
                'Filters': [
                    {'Name': 'tag:Name', 'Values': [self.resource.name]},
                ],
            },
        )

    def add_create_customer_gateway(self):
        return self.add_response(
            'create_customer_gateway',
            service_response={
                'CustomerGateway': {
                    'CustomerGatewayId': self.make_id(self.resource.name),
                },
            },
            expected_params={
                'BgpAsn': 65000,
                'Type': 'ipsec.1',
                'PublicIp': '8.8.8.8',
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

    def add_delete_customer_gateway(self):
        return self.add_response(
            'delete_customer_gateway',
            service_response={},
            expected_params={
                'CustomerGatewayId': self.make_id(self.resource.name),
            },
        )
