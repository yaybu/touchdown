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
from touchdown.tests.stubs.aws import HostedZoneStubber


class TestHostedZoneCreation(StubberTestCase):

    def test_create_hosted_zone(self):
        goal = self.create_goal('apply')

        zone = self.fixtures.enter_context(HostedZoneStubber(
            goal.get_service(
                self.aws.add_hosted_zone(
                    name='example.com',
                ),
                'apply',
            )
        ))

        # This zone doesn't exist yet
        zone.add_list_hosted_zones_empty_response()

        # So create it
        zone.add_create_hosted_zone()

        # Check we managed it
        zone.add_list_hosted_zones_one_response()
        zone.add_list_hosted_zones_one_response()
        zone.add_list_hosted_zones_one_response()

        goal.execute()

    def test_create_hosted_zone_idempotent(self):
        goal = self.create_goal('apply')

        zone = self.fixtures.enter_context(HostedZoneStubber(
            goal.get_service(
                self.aws.add_hosted_zone(
                    name='example.com',
                ),
                'apply',
            )
        ))

        # There is a matching zone deployed at AWS
        zone.add_list_hosted_zones_one_response()

        # There are no rrset - as locally
        zone.add_list_resource_record_sets()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(zone.resource)), 0)


class TestUpdateRrset(StubberTestCase):

    def test_add_rrset(self):
        goal = self.create_goal('apply')

        zone = self.fixtures.enter_context(HostedZoneStubber(
            goal.get_service(
                self.aws.add_hosted_zone(
                    name='example.com',
                    records=[{
                        'name': 'example.com.',
                        'type': 'A',
                        'ttl': 900,
                        'values': ['127.0.0.1'],
                    }],
                ),
                'apply',
            )
        ))

        # There is a matching zone deployed at AWS
        zone.add_list_hosted_zones_one_response()

        # There are no rrset
        zone.add_list_resource_record_sets()

        zone.add_change_resource_record_sets_upsert({
            'Name': 'example.com.',
            'Type': 'A',
            'TTL': 900,
            'ResourceRecords': [{'Value': '127.0.0.1'}],
        })

        goal.execute()

    def test_update_rrset(self):
        goal = self.create_goal('apply')

        zone = self.fixtures.enter_context(HostedZoneStubber(
            goal.get_service(
                self.aws.add_hosted_zone(
                    name='example.com',
                    records=[{
                        'name': 'example.com.',
                        'type': 'A',
                        'ttl': 900,
                        'values': ['192.168.0.1'],
                    }],
                ),
                'apply',
            )
        ))

        # There is a matching zone deployed at AWS
        zone.add_list_hosted_zones_one_response()

        # There is a matching rrset but
        zone.add_list_resource_record_sets([{
            'Name': 'example.com.',
            'Type': 'A',
            'TTL': 900,
            'ResourceRecords': [{'Value': '127.0.0.1'}],
        }])

        zone.add_change_resource_record_sets_upsert({
            'Name': 'example.com.',
            'Type': 'A',
            'TTL': 900,
            'ResourceRecords': [{'Value': '192.168.0.1'}],
        })

        goal.execute()

    def test_delete_rrset(self):
        goal = self.create_goal('apply')

        zone = self.fixtures.enter_context(HostedZoneStubber(
            goal.get_service(
                self.aws.add_hosted_zone(
                    name='example.com',
                    records=[],
                ),
                'apply',
            )
        ))

        # There is a matching zone deployed at AWS
        zone.add_list_hosted_zones_one_response()

        # There is a matching rrset but
        zone.add_list_resource_record_sets([{
            'Name': 'example.com.',
            'Type': 'A',
            'TTL': 900,
            'ResourceRecords': [{'Value': '127.0.0.1'}],
        }])

        zone.add_change_resource_record_sets_delete({
            'Name': 'example.com.',
            'Type': 'A',
            'TTL': 900,
            'ResourceRecords': [{'Value': '127.0.0.1'}],
        })

        goal.execute()


class TestHostedZoneDeletion(StubberTestCase):

    def test_delete_hosted_zone(self):
        goal = self.create_goal('destroy')

        zone = self.fixtures.enter_context(HostedZoneStubber(
            goal.get_service(
                self.aws.add_hosted_zone(
                    name='example.com',
                ),
                'destroy',
            )
        ))

        # There is a matching zone deployed at AWS
        zone.add_list_hosted_zones_one_response()

        # Delete it
        zone.add_delete_hosted_zone()

        goal.execute()

    def test_delete_hosted_zone_idempotent(self):
        goal = self.create_goal('destroy')

        zone = self.fixtures.enter_context(HostedZoneStubber(
            goal.get_service(
                self.aws.add_hosted_zone(
                    name='example.com',
                ),
                'destroy',
            )
        ))

        # There is already no such zone
        zone.add_list_hosted_zones_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(zone.resource)), 0)
