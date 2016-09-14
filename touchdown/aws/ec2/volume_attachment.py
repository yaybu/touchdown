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

from touchdown.aws import common

from touchdown.core import argument
from touchdown.core.plan import Plan, Present
from touchdown.core.resource import Resource

from ..common import SimpleApply, SimpleDescribe, SimpleDestroy, TagsMixin
from .instance import Instance
from .volume import Volume


class VolumeAttachment(Resource):

    resource_name = 'volume_attachment'

    name = argument.Callable(lambda r: ':'.join((r.instance.name, r.device)))

    volume = argument.Resource(Volume, field='VolumeId')
    instance = argument.Resource(Instance, field='InstanceId')
    device = argument.String(field='Device')


class Describe(SimpleDescribe, Plan):

    resource = VolumeAttachment
    service_name = 'ec2'
    api_version = '2015-10-01'
    describe_action = 'describe_volumes'
    describe_envelope = 'Volumes'
    key = 'VolumeId'

    signature = (
        Present('volume'),
        Present('instance'),
        Present('device'),
    )

    def get_describe_filters(self):
        volume = self.runner.get_plan(self.resource.volume)
        if not volume.resource_id:
            return None

        return {
            'VolumeIds': [volume.resource_id]
        }


class Apply(TagsMixin, SimpleApply, Describe):

    create_action = 'attach_volume'
    create_envelope = '@'
    waiter = 'volume_in_use'

    def update_object(self):
        if not self.object:
            return

        instance = self.runner.get_plan(self.resource.instance)
        attachment = None
        for attachment in self.object.get('Attachments', []):
            if attachment['InstanceId'] == instance.resource_id:
                break
            elif attachment['State'] == 'attached':
                yield self.generic_action(
                    'Detaching from instance {}'.format(attachment['InstanceId']),
                    self.client.detach_volume,
                    VolumeId=self.resource_id,
                )
                yield common.Waiter(
                    self,
                    ['Waiting for volume to be detached'],
                    'volume_available',
                    1
                )
                attachment = None
                break

        if not attachment:
            yield self.create_object()
            attachment = {'State': 'attaching'}

        if attachment['State'] == 'attaching':
            yield common.Waiter(
                self,
                ['Waiting for volume to be attached'],
                'volume_in_use',
                1
            )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'detach_volume'
    waiter = 'volume_available'
