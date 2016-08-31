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

from touchdown.tests.stubs.aws import SubnetStubber

from .fixture import AwsFixture


class SubnetFixture(AwsFixture):

    def __init__(self, goal, vpc):
        super(SubnetFixture, self).__init__(goal, vpc.account)
        self.vpc = vpc

    def __enter__(self):
        self.subnet = self.fixtures.enter_context(SubnetStubber(
            self.goal.get_service(
                self.vpc.get_subnet(
                    name='test-route-table',
                    cidr_block='192.168.0.0/25',
                ),
                'describe',
            ),
        ))
        self.subnet.add_describe_subnets_one_response()
        self.subnet.add_describe_network_acls()
        self.subnet.add_describe_route_tables()

        return self.subnet.resource
