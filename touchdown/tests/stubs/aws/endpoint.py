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


class VpcEndpointStubber(ServiceStubber):

    client_service = 'ec2'

    def make_id(self, name):
        return 'vpce-' + super(VpcEndpointStubber, self).make_id(name)[:8]

    def add_describe_vpc_endpoints_one_response_for_vpceid(self, vpceid):
        return self.add_response(
            'describe_vpc_endpoints',
            service_response={
                'VpcEndpoints': [{
                    'VpcEndpointId': vpceid,
                }]
            },
            expected_params={
                'Filters': [
                    {'Name': 'vpc-endpoint-id', 'Values': [vpceid]}
                ]
            },
        )

    def add_describe_vpc_endpoints_empty_response(self, vpceid):
        return self.add_response(
            'describe_vpc_endpoints',
            service_response={
                'VpcEndpoints': [],
            },
            expected_params={
                'Filters': [
                    {'Name': 'vpc-endpoint-id', 'Values': [vpceid]}
                ]
            },
        )

    def add_create_vpc_endpoint(self, vpc_id, route_table_ids, service_name='s3'):
        return self.add_response(
            'create_vpc_endpoint',
            service_response={
                'VpcEndpoint': {
                    'VpcEndpointId': self.make_id(vpc_id + service_name)
                }
            },
            expected_params={
                'VpcId': vpc_id,
                'RouteTableIds': route_table_ids,
                'ServiceName': service_name,
            },
        )

    def add_delete_vpc_endpoint(self, vpce_id):
        return self.add_response(
            'delete_vpc_endpoints',
            service_response={
            },
            expected_params={
                'VpcEndpointIds': [vpce_id],
            },
        )
