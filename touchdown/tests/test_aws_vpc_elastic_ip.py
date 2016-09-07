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

from touchdown.tests.fixtures import ConfigFixture
from touchdown.tests.stubs.aws import ElasticIpStubber

from .aws import StubberTestCase


class TestElasticIpCreation(StubberTestCase):

    def test_create_elastic_ip(self):
        # There is no local state. It should just make a new one.

        goal = self.create_goal('apply')

        config = self.fixtures.enter_context(ConfigFixture(goal, self.workspace))
        public_ip = config.add_string(
            name='network.nat-elastic-ip',
        )

        elastic_ip = self.fixtures.enter_context(ElasticIpStubber(
            goal.get_service(
                self.aws.add_elastic_ip(
                    name='test-elastic_ip',
                    public_ip=public_ip,
                ),
                'apply',
            )
        ))
        elastic_ip.add_allocate_address()

        goal.execute()

    def test_recreate_elastic_ip(self):
        # It should look up 8.8.4.4 (from the local state), find it no longer exists and allocate a new eip

        goal = self.create_goal('apply')

        config = self.fixtures.enter_context(ConfigFixture(goal, self.workspace))
        public_ip = config.add_string(
            name='network.nat-elastic-ip',
        )

        goal.get_service(public_ip, 'set').execute('8.8.4.4')

        elastic_ip = self.fixtures.enter_context(ElasticIpStubber(
            goal.get_service(
                self.aws.add_elastic_ip(
                    name='test-elastic_ip',
                    public_ip=public_ip,
                ),
                'apply',
            )
        ))

        elastic_ip.add_describe_addresses_empty_response('8.8.4.4')
        elastic_ip.add_allocate_address()

        goal.execute()

    def test_create_elastic_ip_idempotent(self):
        # It should look up 8.8.8.8 and find it - there is nothing to do.

        goal = self.create_goal('apply')

        config = self.fixtures.enter_context(ConfigFixture(goal, self.workspace))
        public_ip = config.add_string(
            name='network.nat-elastic-ip',
        )

        goal.get_service(public_ip, 'set').execute('8.8.8.8')

        elastic_ip = self.fixtures.enter_context(ElasticIpStubber(
            goal.get_service(
                self.aws.add_elastic_ip(
                    name='test-elastic_ip',
                    public_ip=public_ip,
                ),
                'apply',
            )
        ))
        elastic_ip.add_describe_addresses_one_response('8.8.8.8')

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(elastic_ip.resource)), 0)


class TestElasticIpDestroy(StubberTestCase):

    def test_destroy_elastic_ip(self):
        # It should look up 8.8.8.8 (from local state) and find it - delete it
        goal = self.create_goal('destroy')

        config = self.fixtures.enter_context(ConfigFixture(goal, self.workspace))
        public_ip = config.add_string(
            name='network.nat-elastic-ip',
        )

        goal.get_service(public_ip, 'set').execute('8.8.8.8')

        elastic_ip = self.fixtures.enter_context(ElasticIpStubber(
            goal.get_service(
                self.aws.add_elastic_ip(
                    name='test-elastic_ip',
                    public_ip=public_ip,
                ),
                'destroy',
            )
        ))
        elastic_ip.add_describe_addresses_one_response('8.8.8.8')
        elastic_ip.add_release_address()

        goal.execute()

    def test_destroy_elastic_ip_idempotent_no_local_state(self):
        # There is no local state - no API calls are made

        goal = self.create_goal('destroy')

        config = self.fixtures.enter_context(ConfigFixture(goal, self.workspace))
        public_ip = config.add_string(
            name='network.nat-elastic-ip',
        )

        elastic_ip = self.fixtures.enter_context(ElasticIpStubber(
            goal.get_service(
                self.aws.add_elastic_ip(
                    name='test-elastic_ip',
                    public_ip=public_ip,
                ),
                'destroy',
            )
        ))

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(elastic_ip.resource)), 0)

    def test_destroy_elastic_ip_idempotent(self):
        # It should look up 8.8.8.8 and not find it. No further API calls.
        goal = self.create_goal('destroy')

        config = self.fixtures.enter_context(ConfigFixture(goal, self.workspace))
        public_ip = config.add_string(
            name='network.nat-elastic-ip',
        )

        goal.get_service(public_ip, 'set').execute('8.8.8.8')

        elastic_ip = self.fixtures.enter_context(ElasticIpStubber(
            goal.get_service(
                self.aws.add_elastic_ip(
                    name='test-elastic_ip',
                    public_ip=public_ip,
                ),
                'destroy',
            )
        ))
        elastic_ip.add_describe_addresses_empty_response('8.8.8.8')

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(elastic_ip.resource)), 0)
