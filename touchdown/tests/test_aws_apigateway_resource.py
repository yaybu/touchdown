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
from touchdown.tests.fixtures.aws import RestApiFixture
from touchdown.tests.stubs.aws import ResourceStubber


class TestCreateResource(StubberTestCase):

    def test_create_resource(self):
        goal = self.create_goal('apply')

        rest_api, rest_api_id = self.fixtures.enter_context(RestApiFixture(goal, self.aws))

        parent = self.fixtures.enter_context(ResourceStubber(
            goal.get_service(
                rest_api.get_resource(
                    name='/',
                ),
                'describe',
            )
        ))
        parent.add_get_resources_one_response(rest_api_id)

        resource = self.fixtures.enter_context(ResourceStubber(
            goal.get_service(
                rest_api.add_resource(
                    name='test-resource',
                    parent_resource=parent.resource,
                ),
                'apply',
            )
        ))
        resource.add_get_resources_empty_response(rest_api_id)
        resource.add_create_resource(
            rest_api_id,
            parent.make_id(parent.resource.name),
        )

        goal.execute()

    def test_create_resource_idempotent(self):
        goal = self.create_goal('apply')

        rest_api, rest_api_id = self.fixtures.enter_context(RestApiFixture(goal, self.aws))

        resource = self.fixtures.enter_context(ResourceStubber(
            goal.get_service(
                rest_api.add_resource(
                    name='test-resource',
                ),
                'apply',
            )
        ))
        resource.add_get_resources_one_response(rest_api_id)

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(resource.resource)), 0)


class TestDestroyResource(StubberTestCase):

    def test_destroy_resource(self):
        goal = self.create_goal('destroy')

        rest_api, rest_api_id = self.fixtures.enter_context(RestApiFixture(goal, self.aws))

        resource = self.fixtures.enter_context(ResourceStubber(
            goal.get_service(
                rest_api.add_resource(
                    name='test-resource',
                ),
                'destroy',
            )
        ))
        resource.add_get_resources_one_response(rest_api_id)
        resource.add_delete_resource(rest_api_id)

        goal.execute()

    def test_destroy_resource_idempotent(self):
        goal = self.create_goal('destroy')

        rest_api, rest_api_id = self.fixtures.enter_context(RestApiFixture(goal, self.aws))

        resource = self.fixtures.enter_context(ResourceStubber(
            goal.get_service(
                rest_api.add_resource(
                    name='test-resource',
                ),
                'destroy',
            )
        ))
        resource.add_get_resources_empty_response(rest_api_id)

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(resource.resource)), 0)
