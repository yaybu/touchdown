# Copyright 2016 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the 'License');
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

from botocore.stub import Stubber

from touchdown.tests.aws import StubberTestCase


class TestVolumeCreation(StubberTestCase):

    def test_create_volume(self):
        goal = self.create_goal('apply')

        volume = self.aws.add_volume(
            name='myvolume',
            availability_zone='eu-west-1a',
        )
        applicator = goal.get_service(volume, 'apply')

        with Stubber(applicator.client) as stub:
            stub.add_response(
                'describe_volumes',
                service_response={
                    'Volumes': [],
                },
                expected_params={
                    'Filters': [
                        {'Name': 'tag:Name', 'Values': ['myvolume']}
                    ],
                },
            )
            stub.add_response(
                'create_volume',
                service_response={
                    'VolumeId': 'vol-abcdef12345',
                },
                expected_params={
                    'AvailabilityZone': 'eu-west-1a',
                },
            )
            stub.add_response(
                'create_tags',
                service_response={
                },
                expected_params={
                    'Resources': ['vol-abcdef12345'],
                    'Tags': [
                        {'Key': 'Name', 'Value': 'myvolume'}
                    ]
                },
            )

            goal.execute()

    def test_create_volume_idempotent(self):
        goal = self.create_goal('apply')

        volume = self.aws.add_volume(
            name='myvolume',
            availability_zone='eu-west-1a',
        )
        applicator = goal.get_service(volume, 'apply')

        with Stubber(applicator.client) as stub:
            stub.add_response(
                'describe_volumes',
                service_response={
                    'Volumes': [{
                        'VolumeId': 'vol-abcdef12345',
                    }],
                },
                expected_params={
                    'Filters': [
                        {'Name': 'tag:Name', 'Values': ['myvolume']}
                    ],
                },
            )

            self.assertEqual(len(list(goal.plan())), 0)
            self.assertEqual(len(goal.get_changes(volume)), 0)


class TestVolumeDeletion(StubberTestCase):

    def test_delete_volume(self):
        goal = self.create_goal('destroy')

        volume = self.aws.add_volume(
            name='myvolume',
            availability_zone='eu-west-1a',
        )
        applicator = goal.get_service(volume, 'destroy')

        with Stubber(applicator.client) as stub:
            stub.add_response(
                'describe_volumes',
                service_response={
                    'Volumes': [{
                        'VolumeId': 'vol-abcdef12345',
                    }],
                },
                expected_params={
                    'Filters': [
                        {'Name': 'tag:Name', 'Values': ['myvolume']}
                    ],
                },
            )
            stub.add_response(
                'delete_volume',
                service_response={
                },
                expected_params={
                    'VolumeId': 'vol-abcdef12345',
                },
            )

            goal.execute()

    def test_delete_volume_idempotent(self):
        goal = self.create_goal('destroy')

        volume = self.aws.add_volume(
            name='myvolume',
            availability_zone='eu-west-1a',
        )
        applicator = goal.get_service(volume, 'destroy')

        with Stubber(applicator.client) as stub:
            stub.add_response(
                'describe_volumes',
                service_response={
                    'Volumes': [],
                },
                expected_params={
                    'Filters': [
                        {'Name': 'tag:Name', 'Values': ['myvolume']}
                    ],
                },
            )

            self.assertEqual(len(list(goal.plan())), 0)
            self.assertEqual(len(goal.get_changes(volume)), 0)
