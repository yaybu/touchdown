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

from touchdown.tests.stubs.aws import EC2InstanceStubber, VolumeStubber, VolumeAttachmentStubber


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
        self.fixtures = ExitStack()
        self.addCleanup(self.fixtures.close)

    def test_create_volume_attachment(self):
        volume = self.fixtures.enter_context(VolumeStubber(
            self.goal.get_service(
                self.aws.get_volume(name='my-volume'),
                'describe',
            )
        ))
        volume.add_describe_volumes_one_response_by_name()

        ec2_instance = self.fixtures.enter_context(EC2InstanceStubber(
            self.goal.get_service(
                self.aws.get_ec2_instance(name='my-ec2-instance'),
                'describe',
            )
        ))
        ec2_instance.add_describe_instances_one_response_by_name()

        volume_attachment = self.fixtures.enter_context(VolumeAttachmentStubber(
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
