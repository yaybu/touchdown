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
    EC2InstanceStubber,
    VolumeAttachmentStubber,
    VolumeStubber,
)


class TestVolumeAttachmentCreation(StubberTestCase):

    def test_create_volume_attachment(self):
        goal = self.create_goal('apply')

        volume = self.fixtures.enter_context(VolumeStubber(
            goal.get_service(
                self.aws.get_volume(name='my-volume'),
                'describe',
            )
        ))
        volume.add_describe_volumes_one_response_by_name()

        ec2_instance = self.fixtures.enter_context(EC2InstanceStubber(
            goal.get_service(
                self.aws.get_ec2_instance(name='my-ec2-instance'),
                'describe',
            )
        ))
        ec2_instance.add_describe_instances_one_response_by_name()

        volume_attachment = self.fixtures.enter_context(VolumeAttachmentStubber(
            goal.get_service(
                ec2_instance.resource.add_volume_attachment(
                    volume=volume.resource,
                    device='/foo',
                ),
                'apply',
            )
        ))
        volume_attachment.add_describe_attachments_empty_response_by_instance_and_volume()
        volume_attachment.add_attach_volume(instance_id='i-79ebae15')

        # Assert that it waits for the volume to be attached
        volume_attachment.add_describe_attachments_one_response_by_volume_AVAILABLE()
        volume_attachment.add_describe_attachments_one_response_by_volume_AVAILABLE()
        volume_attachment.add_describe_attachments_one_response_by_volume_INUSE(instance_id='i-79ebae15')

        # It will hit the API again to make sure it's metadata is up to date in this case
        volume_attachment.add_describe_attachments_one_response_by_volume_INUSE(instance_id='i-79ebae15')

        goal.execute()

    def test_update_volume_attachment(self):
        goal = self.create_goal('apply')

        volume = self.fixtures.enter_context(VolumeStubber(
            goal.get_service(
                self.aws.get_volume(name='my-volume'),
                'describe',
            )
        ))
        volume.add_describe_volumes_one_response_by_name()

        ec2_instance = self.fixtures.enter_context(EC2InstanceStubber(
            goal.get_service(
                self.aws.get_ec2_instance(name='my-ec2-instance'),
                'describe',
            )
        ))
        ec2_instance.add_describe_instances_one_response_by_name()

        volume_attachment = self.fixtures.enter_context(VolumeAttachmentStubber(
            goal.get_service(
                ec2_instance.resource.add_volume_attachment(
                    volume=volume.resource,
                    device='/foo',
                ),
                'apply',
            )
        ))
        volume_attachment.add_describe_attachments_one_response_by_volume_INUSE(instance_id='i-abcd1234')
        volume_attachment.add_detach_volume()
        volume_attachment.add_describe_attachments_one_response_by_volume_AVAILABLE()

        volume_attachment.add_attach_volume(instance_id='i-79ebae15')
        volume_attachment.add_describe_attachments_one_response_by_volume_AVAILABLE()
        volume_attachment.add_describe_attachments_one_response_by_volume_INUSE(instance_id='i-79ebae15')

        goal.execute()

    def test_create_volume_attachment_is_idempotent(self):
        goal = self.create_goal('apply')

        volume = self.fixtures.enter_context(VolumeStubber(
            goal.get_service(
                self.aws.get_volume(name='my-volume'),
                'describe',
            )
        ))
        volume.add_describe_volumes_one_response_by_name()

        ec2_instance = self.fixtures.enter_context(EC2InstanceStubber(
            goal.get_service(
                self.aws.get_ec2_instance(name='my-ec2-instance'),
                'describe',
            )
        ))
        ec2_instance.add_describe_instances_one_response_by_name()

        volume_attachment = self.fixtures.enter_context(VolumeAttachmentStubber(
            goal.get_service(
                ec2_instance.resource.add_volume_attachment(
                    volume=volume.resource,
                    device='/foo',
                ),
                'apply',
            )
        ))
        volume_attachment.add_describe_attachments_one_response_by_volume_INUSE(instance_id='i-79ebae15')

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(volume.resource)), 0)


class TestVolumeAttachmentDeletion(StubberTestCase):

    def test_delete_volume_attachment(self):
        goal = self.create_goal('destroy')

        volume = self.fixtures.enter_context(VolumeStubber(
            goal.get_service(
                self.aws.get_volume(name='my-volume'),
                'describe',
            )
        ))
        volume.add_describe_volumes_one_response_by_name()

        ec2_instance = self.fixtures.enter_context(EC2InstanceStubber(
            goal.get_service(
                self.aws.get_ec2_instance(name='my-ec2-instance'),
                'describe',
            )
        ))
        ec2_instance.add_describe_instances_one_response_by_name()

        volume_attachment = self.fixtures.enter_context(VolumeAttachmentStubber(
            goal.get_service(
                ec2_instance.resource.add_volume_attachment(
                    volume=volume.resource,
                    device='/foo',
                ),
                'destroy',
            )
        ))
        volume_attachment.add_describe_attachments_one_response_by_volume_INUSE(instance_id='i-79ebae15')
        volume_attachment.add_detach_volume()

        # Assert that it waits for the volume to be detached
        volume_attachment.add_describe_attachments_one_response_by_volume_INUSE(instance_id='i-79ebae15')
        volume_attachment.add_describe_attachments_one_response_by_volume_INUSE(instance_id='i-79ebae15')
        volume_attachment.add_describe_attachments_one_response_by_volume_AVAILABLE()

        goal.execute()

    def test_delete_volume_attachment_is_idempotent(self):
        goal = self.create_goal('destroy')

        volume = self.fixtures.enter_context(VolumeStubber(
            goal.get_service(
                self.aws.get_volume(name='my-volume'),
                'describe',
            )
        ))
        volume.add_describe_volumes_one_response_by_name()

        ec2_instance = self.fixtures.enter_context(EC2InstanceStubber(
            goal.get_service(
                self.aws.get_ec2_instance(name='my-ec2-instance'),
                'describe',
            )
        ))
        ec2_instance.add_describe_instances_one_response_by_name()

        volume_attachment = self.fixtures.enter_context(VolumeAttachmentStubber(
            goal.get_service(
                ec2_instance.resource.add_volume_attachment(
                    volume=volume.resource,
                    device='/foo',
                ),
                'destroy',
            )
        ))
        volume_attachment.add_describe_attachments_empty_response_by_instance_and_volume()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(volume.resource)), 0)
