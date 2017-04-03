# Copyright 2017 Isotoma Limited
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

from touchdown.tests.stubs.aws import InstanceProfileStubber

from .fixture import AwsFixture


class InstanceProfileFixture(AwsFixture):

    def __enter__(self):
        self.profile = self.fixtures.enter_context(InstanceProfileStubber(
            self.goal.get_service(
                self.aws.get_instance_profile(
                    name='my-test-profile',
                ),
                'describe',
            ),
        ))
        self.profile.add_list_instance_profile_one_response()

        return self.profile.resource
