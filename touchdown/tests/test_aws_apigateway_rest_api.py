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
from touchdown.tests.stubs.aws import RestApiStubber


class TestCreateRestApi(StubberTestCase):

    def test_create_rest_api(self):
        goal = self.create_goal('apply')

        rest_api = self.fixtures.enter_context(RestApiStubber(
            goal.get_service(
                self.aws.add_rest_api(
                    name='test-rest_api',
                ),
                'apply',
            )
        ))
        rest_api.add_get_rest_apis_empty_response()
        rest_api.add_create_rest_api()

        goal.execute()

    def test_create_rest_api_idempotent(self):
        goal = self.create_goal('apply')

        rest_api = self.fixtures.enter_context(RestApiStubber(
            goal.get_service(
                self.aws.add_rest_api(
                    name='test-rest_api',
                ),
                'apply',
            )
        ))
        rest_api.add_get_rest_apis_one_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(rest_api.resource)), 0)


class TestDestroyRestApi(StubberTestCase):

    def test_destroy_rest_api(self):
        goal = self.create_goal('destroy')

        rest_api = self.fixtures.enter_context(RestApiStubber(
            goal.get_service(
                self.aws.add_rest_api(
                    name='test-rest_api',
                ),
                'destroy',
            )
        ))
        rest_api.add_get_rest_apis_one_response()
        rest_api.add_delete_rest_api()

        goal.execute()

    def test_destroy_rest_api_idempotent(self):
        goal = self.create_goal('destroy')

        rest_api = self.fixtures.enter_context(RestApiStubber(
            goal.get_service(
                self.aws.add_rest_api(
                    name='test-rest_api',
                ),
                'destroy',
            )
        ))
        rest_api.add_get_rest_apis_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(rest_api.resource)), 0)
