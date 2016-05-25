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


class RouteTableStubber(ServiceStubber):

    client_service = 'ec2'

    def make_id(self, name):
        return 'rt-' + super(RouteTableStubber, self).make_id(name)[:8]

    def add_describe_route_tables_one_response_by_name(self):
        return self.add_response(
            'describe_route_tables',
            service_response={
                'RouteTables': [{
                    'RouteTableId': self.make_id(self.resource.name),
                }],
            },
            expected_params={
                'Filters': [
                    {'Name': 'tag:Name', 'Values': [self.resource.name]}
                ],
            },
        )
