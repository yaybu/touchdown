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

from touchdown.tests.stubs.aws import RouteTableStubber

from .fixture import AwsFixture


class RouteTableFixture(AwsFixture):

    def __init__(self, goal, aws, vpc):
        super(RouteTableFixture, self).__init__(goal, aws)
        self.vpc = vpc

    def __enter__(self):
        self.route_table = self.fixtures.enter_context(RouteTableStubber(
            self.goal.get_service(
                self.vpc.get_route_table(
                    name='test-route-table',
                ),
                'describe',
            ),
        ))
        self.route_table.add_describe_route_tables_one_response_by_name()

        return self.route_table.resource
