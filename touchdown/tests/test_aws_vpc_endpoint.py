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
from touchdown.tests.fixtures.aws import VpcFixture
from touchdown.tests.stubs import TemporaryFolder
from touchdown.tests.stubs.aws import RouteTableStubber, VpcEndpointStubber


class TestVpcEndpoint(StubberTestCase):

    def test_create_endpoint(self):
        # The VPC and RouteTable already exist
        # There is no local state describing a VPCE
        # Therfore a VPCE is created
        goal = self.create_goal('apply')

        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        route_table = self.fixtures.enter_context(RouteTableStubber(
            goal.get_service(
                vpcf.vpc.get_route_table(name='test-route-table'),
                'describe',
            )
        ))
        route_table.add_describe_route_tables_one_response_by_name()

        folder = self.workspace.add_local_folder(
            name=self.fixtures.enter_context(TemporaryFolder()).folder,
        )
        config = folder.add_file(name='text.cfg').add_ini_file()
        name = config.add_string(name='vpc.endpoint-id')

        endpoint = self.fixtures.enter_context(VpcEndpointStubber(
            goal.get_service(
                vpcf.vpc.add_endpoint(
                    name='is-this-even-used',
                    id=name,
                    service='s3',
                    route_tables=[route_table.resource],
                ),
                'apply',
            )
        ))
        endpoint.add_create_vpc_endpoint(
            vpcf.vpc_id,
            [route_table.make_id(route_table.resource.name)],
        )

        goal.execute()

    def test_create_endpoint_recreate(self):
        # The VPC and RouteTable already exist
        # There is local state describing a VPCE but it does not exist
        # Therefore a VPCE is created

        goal = self.create_goal('apply')

        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        route_table = self.fixtures.enter_context(RouteTableStubber(
            goal.get_service(
                vpcf.vpc.get_route_table(name='test-route-table'),
                'describe',
            )
        ))
        route_table.add_describe_route_tables_one_response_by_name()

        folder = self.workspace.add_local_folder(
            name=self.fixtures.enter_context(TemporaryFolder()).folder,
        )
        config = folder.add_file(name='text.cfg').add_ini_file()
        name = config.add_string(name='vpc.endpoint-id')

        goal.get_service(name, 'set').execute('vpce-1234abcd')

        endpoint = self.fixtures.enter_context(VpcEndpointStubber(
            goal.get_service(
                vpcf.vpc.add_endpoint(
                    name='is-this-even-used',
                    id=name,
                    service='s3',
                    route_tables=[route_table.resource],
                ),
                'apply',
            )
        ))

        endpoint.add_describe_vpc_endpoints_empty_response('vpce-1234abcd')
        endpoint.add_create_vpc_endpoint(
            vpcf.vpc_id,
            [route_table.make_id(route_table.resource.name)],
        )

        goal.execute()

    def test_create_endpoint_idempotent(self):
        # The VPC and RouteTable already exist
        # There is local state describing a VPCE and it does exist
        # Therefore no VPCE is created

        goal = self.create_goal('apply')

        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        route_table = self.fixtures.enter_context(RouteTableStubber(
            goal.get_service(
                vpcf.vpc.get_route_table(name='test-route-table'),
                'describe',
            )
        ))
        route_table.add_describe_route_tables_one_response_by_name()

        folder = self.workspace.add_local_folder(
            name=self.fixtures.enter_context(TemporaryFolder()).folder,
        )
        config = folder.add_file(name='text.cfg').add_ini_file()
        name = config.add_string(name='vpc.endpoint-id')

        goal.get_service(name, 'set').execute('vpce-1234abcd')

        endpoint = self.fixtures.enter_context(VpcEndpointStubber(
            goal.get_service(
                vpcf.vpc.add_endpoint(
                    name='is-this-even-used',
                    id=name,
                    service='s3',
                    route_tables=[route_table.resource],
                ),
                'apply',
            )
        ))
        endpoint.add_describe_vpc_endpoints_one_response_for_vpceid('vpce-1234abcd')

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(endpoint.resource)), 0)

    def test_destroy_endpoint(self):
        # The VPC and RouteTable already exist
        # There is local state describing a VPCE and it does exist
        # Therefore VPCE is destroyed

        goal = self.create_goal('destroy')

        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        route_table = self.fixtures.enter_context(RouteTableStubber(
            goal.get_service(
                vpcf.vpc.get_route_table(name='test-route-table'),
                'describe',
            )
        ))
        route_table.add_describe_route_tables_one_response_by_name()

        folder = self.workspace.add_local_folder(
            name=self.fixtures.enter_context(TemporaryFolder()).folder,
        )
        config = folder.add_file(name='text.cfg').add_ini_file()
        name = config.add_string(name='vpc.endpoint-id')

        goal.get_service(name, 'set').execute('vpce-1234abcd')

        endpoint = self.fixtures.enter_context(VpcEndpointStubber(
            goal.get_service(
                vpcf.vpc.add_endpoint(
                    name='is-this-even-used',
                    id=name,
                    service='s3',
                    route_tables=[route_table.resource],
                ),
                'destroy',
            )
        ))
        endpoint.add_describe_vpc_endpoints_one_response_for_vpceid('vpce-1234abcd')
        endpoint.add_delete_vpc_endpoint('vpce-1234abcd')

        goal.execute()

    def test_destroy_endpoint_no_local_state(self):
        # The VPC and RouteTable already exist
        # There is no local state describing a VPCE
        # Therefore no VPCE is destroyed

        goal = self.create_goal('destroy')

        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        route_table = self.fixtures.enter_context(RouteTableStubber(
            goal.get_service(
                vpcf.vpc.get_route_table(name='test-route-table'),
                'describe',
            )
        ))
        route_table.add_describe_route_tables_one_response_by_name()

        folder = self.workspace.add_local_folder(
            name=self.fixtures.enter_context(TemporaryFolder()).folder,
        )
        config = folder.add_file(name='text.cfg').add_ini_file()
        name = config.add_string(name='vpc.endpoint-id')

        endpoint = self.fixtures.enter_context(VpcEndpointStubber(
            goal.get_service(
                vpcf.vpc.add_endpoint(
                    name='is-this-even-used',
                    id=name,
                    service='s3',
                    route_tables=[route_table.resource],
                ),
                'destroy',
            )
        ))

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(endpoint.resource)), 0)

    def test_destroy_endpoint_idempotent(self):
        # The VPC and RouteTable already exist
        # There is local state describing a VPCE and it does not exist
        # Therefore no VPCE is destroyed

        goal = self.create_goal('destroy')

        vpcf = self.fixtures.enter_context(VpcFixture(goal, self.aws))

        route_table = self.fixtures.enter_context(RouteTableStubber(
            goal.get_service(
                vpcf.vpc.get_route_table(name='test-route-table'),
                'describe',
            )
        ))
        route_table.add_describe_route_tables_one_response_by_name()

        folder = self.workspace.add_local_folder(
            name=self.fixtures.enter_context(TemporaryFolder()).folder,
        )
        config = folder.add_file(name='text.cfg').add_ini_file()
        name = config.add_string(name='vpc.endpoint-id')

        goal.get_service(name, 'set').execute('vpce-1234abcd')

        endpoint = self.fixtures.enter_context(VpcEndpointStubber(
            goal.get_service(
                vpcf.vpc.add_endpoint(
                    name='is-this-even-used',
                    id=name,
                    service='s3',
                    route_tables=[route_table.resource],
                ),
                'destroy',
            )
        ))
        endpoint.add_describe_vpc_endpoints_empty_response('vpce-1234abcd')

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(endpoint.resource)), 0)
