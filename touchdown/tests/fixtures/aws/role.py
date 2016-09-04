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

from touchdown.tests.stubs.aws import RoleStubber

from .fixture import AwsFixture


class RoleFixture(AwsFixture):

    def __enter__(self):
        self.role = self.fixtures.enter_context(RoleStubber(
            self.goal.get_service(
                self.aws.get_role(
                    name='my-test-role',
                ),
                'describe',
            ),
        ))
        self.role.add_list_roles_one_response_by_name()

        return self.role.resource
