# Copyright 2015 Isotoma Limited
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

from touchdown.tests.aws import StubberTestCase
from touchdown.tests.stubs import TemporaryFolder
from touchdown.tests.stubs.aws import (
    RouteTableStubber,
    VpcEndpointStubber,
    VpcStubber,
)


class TestVpcEndpoint(StubberTestCase):

    def test_create_endpoint(self):
        goal = self.create_goal('apply')

        vpc = self.fixtures.enter_context(VpcStubber(
            goal.get_service(
                self.aws.get_vpc(name='test-vpc'),
                'describe',
            )
        ))
        vpc.add_describe_vpcs_one_response_by_name()

        route_table = self.fixtures.enter_context(RouteTableStubber(
            goal.get_service(
                vpc.resource.get_route_table(name='test-route-table'),
                'describe',
            )
        ))
        route_table.add_describe_route_tables_one_response_by_name()

        folder = self.workspace.add_local_folder(
            name=self.fixtures.enter_context(TemporaryFolder()).folder,
        )
        config = folder.add_file(name="text.cfg").add_ini_file()
        name = config.add_string(name="vpc.endpoint-id")

        endpoint = self.fixtures.enter_context(VpcEndpointStubber(
            goal.get_service(
                vpc.resource.add_endpoint(
                    name='is-this-even-used',
                    id=name,
                    service='s3',
                    route_tables=[route_table.resource],
                ),
                'apply',
            )
        ))
        endpoint.add_create_vpc_endpoint(
            vpc.make_id(vpc.resource.name),
            [route_table.make_id(route_table.resource.name)],
        )

        goal.execute()
