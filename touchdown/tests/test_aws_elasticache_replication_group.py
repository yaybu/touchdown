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

from touchdown.tests.aws import StubberTestCase
from touchdown.tests.stubs.aws import (
    LaunchConfigurationStubber,
    ReplicationGroupStubber,
)


class TestReplicationGroupCreation(StubberTestCase):

    def test_create_replication_group(self):
        goal = self.create_goal('apply')

        replication_group = self.fixtures.enter_context(ReplicationGroupStubber(
            goal.get_service(
                self.aws.add_replication_group(
                    name='my-rep_group',
                ),
                'apply',
            )
        ))
        replication_group.add_describe_replication_groups_empty_response()
        replication_group.add_create_replication_group()
        replication_group.add_describe_replication_groups_one_response(status='creating')
        replication_group.add_describe_replication_groups_one_response()
        replication_group.add_describe_replication_groups_one_response()

        goal.execute()

    def test_create_replication_group_idempotent(self):
        goal = self.create_goal('apply')

        replication_group = self.fixtures.enter_context(ReplicationGroupStubber(
            goal.get_service(
                self.aws.add_replication_group(
                    name='my-rep_group',
                ),
                'apply',
            )
        ))
        replication_group.add_describe_replication_groups_one_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(replication_group.resource)), 0)


class TestReplicationGroupDeletion(StubberTestCase):

    def test_delete_replication_group(self):
        goal = self.create_goal('destroy')

        replication_group = self.fixtures.enter_context(ReplicationGroupStubber(
            goal.get_service(
                self.aws.add_replication_group(
                    name='my-rep_group',
                ),
                'destroy',
            )
        ))
        replication_group.add_describe_replication_groups_one_response()
        replication_group.add_delete_replication_group()

        # Wait for it to go away
        replication_group.add_describe_replication_groups_one_response()
        replication_group.add_describe_replication_groups_empty_response()

        goal.execute()

    def test_delete_replication_group_idempotent(self):
        goal = self.create_goal('destroy')

        replication_group = self.fixtures.enter_context(ReplicationGroupStubber(
            goal.get_service(
                self.aws.add_replication_group(
                    name='my-rep_group',
                ),
                'destroy',
            )
        ))
        replication_group.add_describe_replication_groups_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(replication_group.resource)), 0)


class TestReplicationGroupComplications(StubberTestCase):

    def test_with_launch_configuration(self):
        goal = self.create_goal('apply')

        replication_group = self.fixtures.enter_context(ReplicationGroupStubber(
            goal.get_service(
                self.aws.add_replication_group(
                    name='my-rep_group',
                ),
                'apply',
            )
        ))
        replication_group.add_describe_replication_groups_empty_response()
        replication_group.add_create_replication_group()
        replication_group.add_describe_replication_groups_one_response(status='creating')
        replication_group.add_describe_replication_groups_one_response()
        replication_group.add_describe_replication_groups_one_response()

        launch_config = self.fixtures.enter_context(LaunchConfigurationStubber(
            goal.get_service(
                self.aws.add_launch_configuration(
                    name='my-test-lc',
                    image='ami-cba130bc',
                    instance_type='t2.micro',
                    json_user_data={
                        'REDIS_ADDRESS': replication_group.resource.endpoint_address,
                        'REDIS_PORT': replication_group.resource.endpoint_port,
                    }
                ),
                'apply',
            )
        ))

        user_data = (
            '{"REDIS_ADDRESS": "myreplgrp.q68zge.ng.0001.use1devo.elmo-dev.amazonaws.com", '
            '"REDIS_PORT": 6379}'
        )

        launch_config.add_describe_launch_configurations_empty_response()
        launch_config.add_describe_launch_configurations_empty_response()
        launch_config.add_create_launch_configuration(user_data=user_data)
        launch_config.add_describe_launch_configurations_one_response(user_data=user_data)
        launch_config.add_describe_launch_configurations_one_response(user_data=user_data)
        launch_config.add_describe_launch_configurations_one_response(user_data=user_data)

        goal.execute()
