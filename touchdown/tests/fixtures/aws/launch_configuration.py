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

from touchdown.tests.stubs.aws import LaunchConfigurationStubber

from .fixture import AwsFixture


class LaunchConfigurationFixture(AwsFixture):

    def __enter__(self):
        self.launch_config = self.fixtures.enter_context(LaunchConfigurationStubber(
            self.goal.get_service(
                self.aws.add_launch_configuration(
                    name='my-test-lc',
                    image='ami-cba130bc',
                    instance_type='t2.micro',
                ),
                'apply',
            )
        ))

        self.launch_config.add_describe_launch_configurations_one_response()
        self.launch_config.add_describe_launch_configurations_one_response()
        self.launch_config.add_describe_auto_scaling_groups()

        return self.launch_config.resource
