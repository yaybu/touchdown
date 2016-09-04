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


class LoadBalancerStubber(ServiceStubber):

    client_service = 'elb'

    def add_describe_load_balancers_empty(self):
        return self.add_response(
            'describe_load_balancers',
            service_response={},
            expected_params={
                'LoadBalancerNames': [self.resource.name],
            },
        )

    def add_describe_load_balancers_one(self):
        return self.add_response(
            'describe_load_balancers',
            service_response={
                'LoadBalancerDescriptions': [{
                    'LoadBalancerName': self.resource.name,
                    'CanonicalHostedZoneName': 'mystack-myelb-15HMABG9ZCN57-1013119603.us-east-1.elb.amazonaws.com',
                    'CanonicalHostedZoneNameID': 'Z3DZXE0Q79N41H',
                    'DNSName': 'mystack-myelb-15HMABG9ZCN57-1013119603.us-east-1.elb.amazonaws.com',
                }]
            },
            expected_params={
                'LoadBalancerNames': [self.resource.name],
            },
        )

    def add_describe_load_balancer_attributes(self):
        return self.add_response(
            'describe_load_balancer_attributes',
            service_response={
                'LoadBalancerAttributes': {
                },
            },
            expected_params={
                'LoadBalancerName': self.resource.name,
            },
        )

    def add_create_load_balancer(self):
        return self.add_response(
            'create_load_balancer',
            service_response={},
            expected_params={
                'LoadBalancerName': self.resource.name,
                'Listeners': [],
            },
        )

    def add_delete_load_balancer(self):
        return self.add_response(
            'delete_load_balancer',
            service_response={},
            expected_params={
                'LoadBalancerName': self.resource.name,
            },
        )
