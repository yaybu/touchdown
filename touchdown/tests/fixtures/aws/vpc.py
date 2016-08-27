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

from touchdown.tests.stubs.aws import VpcStubber

from .fixture import AwsFixture


class VpcFixture(AwsFixture):

    def __enter__(self):
        self.vpc = self.fixtures.enter_context(VpcStubber(
            self.goal.get_service(
                self.aws.get_vpc(
                    name='test-vpc',
                    cidr_block='192.168.0.0/25',
                ),
                'describe',
            ),
        ))
        self.vpc.add_describe_vpcs_one_response_by_name()

        return self.vpc.resource
