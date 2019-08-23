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


class VpnConnectionStubber(ServiceStubber):

    client_service = "ec2"

    def add_describe_vpn_connections_empty_response(self):
        return self.add_response(
            "describe_vpn_connections",
            service_response={},
            expected_params={
                "Filters": [{"Name": "tag:Name", "Values": [self.resource.name]}]
            },
        )

    def add_describe_vpn_connections_one_response(self, state="available"):
        return self.add_response(
            "describe_vpn_connections",
            service_response={
                "VpnConnections": [
                    {
                        "VpnConnectionId": self.make_id(self.resource.name),
                        "State": state,
                    }
                ]
            },
            expected_params={
                "Filters": [{"Name": "tag:Name", "Values": [self.resource.name]}]
            },
        )

    def add_create_vpn_connection(self, customer_gateway_id, vpn_gateway_id):
        return self.add_response(
            "create_vpn_connection",
            service_response={
                "VpnConnection": {"VpnConnectionId": self.make_id(self.resource.name)}
            },
            expected_params={
                "Options": {"StaticRoutesOnly": True},
                "Type": "ipsec.1",
                "VpnGatewayId": vpn_gateway_id,
                "CustomerGatewayId": customer_gateway_id,
            },
        )

    def add_create_tags(self, **tags):
        tag_list = [{"Key": k, "Value": v} for (k, v) in tags.items()]
        self.add_response(
            "create_tags",
            service_response={},
            expected_params={
                "Resources": [self.make_id(self.resource.name)],
                "Tags": tag_list,
            },
        )

    def add_delete_vpn_connection(self):
        return self.add_response(
            "delete_vpn_connection",
            service_response={},
            expected_params={"VpnConnectionId": self.make_id(self.resource.name)},
        )
