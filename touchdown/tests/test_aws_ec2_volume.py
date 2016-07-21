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

import unittest

from botocore.stub import Stubber

from touchdown import frontends
from touchdown.core import goals, workspace
from touchdown.core.map import SerialMap


class TestVolumeCreation(unittest.TestCase):

    def setUp(self):
        self.workspace = workspace.Workspace()
        self.aws = self.workspace.add_aws(access_key_id='dummy', secret_access_key='dummy', region='eu-west-1')
        self.goal = goals.create(
            'apply',
            self.workspace,
            frontends.ConsoleFrontend(interactive=False),
            map=SerialMap
        )

    def test_create_volume(self):
        volume = self.aws.add_volume(
            name='myvolume',
            availability_zone='eu-west-1a',
        )
        applicator = self.goal.get_service(volume, 'apply')

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

            self.goal.execute()

    def test_create_volume_idempotent(self):
        volume = self.aws.add_volume(
            name='myvolume',
            availability_zone='eu-west-1a',
        )
        applicator = self.goal.get_service(volume, 'apply')

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

            self.assertEqual(len(list(self.goal.plan())), 0)
            self.assertEqual(len(self.goal.get_changes(volume)), 0)


class TestVolumeDeletion(unittest.TestCase):

    def setUp(self):
        self.workspace = workspace.Workspace()
        self.aws = self.workspace.add_aws(access_key_id='dummy', secret_access_key='dummy', region='eu-west-1')
        self.goal = goals.create(
            'destroy',
            self.workspace,
            frontends.ConsoleFrontend(interactive=False),
            map=SerialMap
        )

    def test_delete_volume(self):
        volume = self.aws.add_volume(
            name='myvolume',
            availability_zone='eu-west-1a',
        )
        applicator = self.goal.get_service(volume, 'destroy')

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

            self.goal.execute()

    def test_delete_volume_idempotent(self):
        volume = self.aws.add_volume(
            name='myvolume',
            availability_zone='eu-west-1a',
        )
        applicator = self.goal.get_service(volume, 'destroy')

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

            self.assertEqual(len(list(self.goal.plan())), 0)
            self.assertEqual(len(self.goal.get_changes(volume)), 0)
