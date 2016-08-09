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
from contextlib2 import ExitStack
from botocore.stub import Stubber

from touchdown import frontends
from touchdown.core import goals, workspace
from touchdown.core.map import SerialMap


class ServiceStubber(Stubber):

    def __init__(self, service):
        self.resource = service.resource
        self.service = service
        # assert service.client.service == self.client_service
        super(ServiceStubber, self).__init__(service.client)


class VolumeStubber(ServiceStubber):

    client_service = 'ec2'

    def add_describe_volumes_empty_response_by_name(self):
        return self.add_response(
            'describe_volumes',
            service_response={
                'Volumes': [],
            },
            expected_params={
                'Filters': [
                    {'Name': 'tag:Name', 'Values': [self.resource.name]}
                ],
            },
        )

    def add_describe_volumes_one_response_by_name(self):
        return self.add_response(
            'describe_volumes',
            service_response={
                'Volumes': [{
                    'VolumeId': 'vol-abcdef12345',
                }],
            },
            expected_params={
                'Filters': [
                    {'Name': 'tag:Name', 'Values': [self.resource.name]}
                ],
            },
        )


class EC2InstanceStubber(ServiceStubber):

    client_service = 'ec2'

    def add_describe_instances_empty_response_by_name(self):
        return self.add_response(
            'describe_instances',
            service_response={
                'Reservations': [],
            },
            expected_params={
                'Filters': [
                    {'Name': 'tag:Name', 'Values': [self.resource.name]},
                    {'Name': 'instance-state-name', 'Values': ['pending', 'running']},
                ],
            },
        )

    def add_describe_instances_one_response_by_name(self):
        return self.add_response(
            'describe_instances',
            service_response={
                'Reservations': [{
                    'Instances': [{
                        'InstanceId': 'i-abcdef12345',
                    }],
                }]
            },
            expected_params={
                'Filters': [
                    {'Name': 'tag:Name', 'Values': [self.resource.name]},
                    {'Name': 'instance-state-name', 'Values': ['pending', 'running']},
                ],
            },
        )


class VolumeAttachmentStubber(ServiceStubber):

    def add_describe_attachments_empty_response_by_instance_and_volume(self):
        return self.add_response(
            'describe_volumes',
            service_response={
                'Volumes': [],
            },
            expected_params={
                'Filters': [
                    {'Name': 'attachment.status', 'Values': ['attaching', 'attached']},
                    {'Name': 'attachment.instance-id', 'Values': ['i-abcdef12345']}
                ],
                'VolumeIds': ['vol-abcdef12345'],
            }
        )

    def add_attach_volume(self, device='/foo'):
        return self.add_response(
            'attach_volume',
            service_response={
            },
            expected_params={
                'Device': device,
                'InstanceId': 'i-abcdef12345',
                'VolumeId': 'vol-abcdef12345',
            }
        )


class TestVolumeAttachmentCreation(unittest.TestCase):

    def setUp(self):
        self.workspace = workspace.Workspace()
        self.aws = self.workspace.add_aws(access_key_id='dummy', secret_access_key='dummy', region='eu-west-1')
        self.goal = goals.create(
            'apply',
            self.workspace,
            frontends.ConsoleFrontend(interactive=False),
            map=SerialMap
        )

    def test_create_volume_attachment(self):
        with ExitStack() as stack:
            volume = stack.enter_context(VolumeStubber(
                self.goal.get_service(
                    self.aws.get_volume(name='my-volume'),
                    'describe',
                )
            ))
            volume.add_describe_volumes_one_response_by_name()

            ec2_instance = stack.enter_context(EC2InstanceStubber(
                self.goal.get_service(
                    self.aws.get_ec2_instance(name='my-ec2-instance'),
                    'describe',
                )
            ))
            ec2_instance.add_describe_instances_one_response_by_name()

            volume_attachment = stack.enter_context(VolumeAttachmentStubber(
                self.goal.get_service(
                    ec2_instance.resource.add_volume_attachment(
                        volume=volume.resource,
                        device='/foo',
                    ),
                    'apply',
                )
            ))
            volume_attachment.add_describe_attachments_empty_response_by_instance_and_volume()
            volume_attachment.add_attach_volume()

            self.goal.execute()
