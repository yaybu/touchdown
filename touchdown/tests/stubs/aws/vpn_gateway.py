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


class VpnGatewayStubber(ServiceStubber):

    client_service = 'ec2'

    def make_id(self, name):
        return 'vgw-' + super(VpnGatewayStubber, self).make_id(name)[:8]

    def add_describe_vpn_gateways_empty_response(self):
        return self.add_response(
            'describe_vpn_gateways',
            service_response={},
            expected_params={
                'Filters': [
                    {'Name': 'tag:Name', 'Values': [self.resource.name]},
                ],
            },
        )

    def add_describe_vpn_gateways_one_response(self, state='available', attachments=None):
        return self.add_response(
            'describe_vpn_gateways',
            service_response={
                'VpnGateways': [{
                    'VpnGatewayId': self.make_id(self.resource.name),
                    'State': state,
                    'VpcAttachments': attachments or [],
                }]
            },
            expected_params={
                'Filters': [
                    {'Name': 'tag:Name', 'Values': [self.resource.name]},
                ],
            },
        )

    def add_create_vpn_gateway(self):
        return self.add_response(
            'create_vpn_gateway',
            service_response={
                'VpnGateway': {
                    'VpnGatewayId': self.make_id(self.resource.name),
                },
            },
            expected_params={
                'Type': 'ipsec.1',
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

    def add_attach_vpn_gateway(self, vpc_id):
        return self.add_response(
            'attach_vpn_gateway',
            service_response={},
            expected_params={
                'VpcId': vpc_id,
                'VpnGatewayId': self.make_id(self.resource.name),
            },
        )

    def add_delete_vpn_gateway(self):
        return self.add_response(
            'delete_vpn_gateway',
            service_response={},
            expected_params={
                'VpnGatewayId': self.make_id(self.resource.name),
            },
        )
