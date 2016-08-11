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
    describe_action = 'describe_volumes'
    describe_envelope = 'Volumes'
    key = 'VolumeId'

    def get_describe_filters(self):
        volume = self.runner.get_plan(self.resource.volume)
        instance = self.runner.get_plan(self.resource.instance)
        if not volume.resource_id or not instance.resource_id:
            return None

        return {
            'VolumeIds': [volume.resource_id],
            'Filters': [
                {
                    'Name': 'attachment.status',
                    'Values': ['attaching', 'attached'],
                },
                {
                    'Name': 'attachment.instance-id',
                    'Values': [instance.resource_id],
                },
            ]
        }


class Apply(TagsMixin, SimpleApply, Describe):

    create_action = 'attach_volume'
    create_envelope = '@'
    signature = (
        Present('volume'),
        Present('instance'),
        Present('device'),
    )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'detach_volume'
    signature = (
        Present('volume'),
        Present('instance'),
        Present('device'),
    )
