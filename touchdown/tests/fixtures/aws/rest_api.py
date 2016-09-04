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

from touchdown.tests.stubs.aws import RestApiStubber

from .fixture import AwsFixture


class RestApiFixture(AwsFixture):

    def __enter__(self):
        self.rest_api = self.fixtures.enter_context(RestApiStubber(
            self.goal.get_service(
                self.aws.get_rest_api(
                    name='my-test-rest_api',
                ),
                'describe',
            ),
        ))
        self.rest_api.add_get_rest_apis_one_response()

        return self.rest_api.resource, self.rest_api.make_id(self.rest_api.resource.name)
