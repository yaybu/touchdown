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

from touchdown.tests.stubs.aws import NetworkAclStubber

from .fixture import AwsFixture


class NetworkAclFixture(AwsFixture):

    def __init__(self, goal, aws, vpc):
        super(NetworkAclFixture, self).__init__(goal, aws)
        self.vpc = vpc

    def __enter__(self):
        self.network_acl = self.fixtures.enter_context(NetworkAclStubber(
            self.goal.get_service(
                self.vpc.get_network_acl(
                    name='test-network-acl',
                ),
                'describe',
            ),
        ))
        self.network_acl.add_describe_network_acls_one_response_by_name()

        return self.network_acl.resource
