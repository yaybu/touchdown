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

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy, TagsMixin
from ..kms import Key


class Volume(Resource):

    resource_name = 'volume'

    name = argument.String(min=3, max=128, field='Name', group='tags')

    size = argument.Integer(field='Size', min=1, max=16384)
    availability_zone = argument.String(field='AvailabilityZone')
    volume_type = argument.String(field='VolumeType', choices=['gp2', 'io1', 'st1', 'standard'])
    iops = argument.Integer(field='Iops')

    key = argument.Resource(Key, field='KmsKeyId')

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = Volume
    service_name = 'ec2'
    api_version = '2015-10-01'
    describe_action = 'describe_volumes'
    describe_notfound_exception = 'InvalidVolume.NotFound'
    describe_envelope = 'Volumes'
    key = 'VolumeId'

    def get_describe_filters(self):
        return {'Filters': [{'Name': 'tag:Name', 'Values': [self.resource.name]}]}


class Apply(TagsMixin, SimpleApply, Describe):

    create_action = 'create_volume'
    create_envelope = '@'
    waiter = 'volume_available'
    signature = (
        Present('name'),
        Present('availability_zone')
    )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_volume'
    waiter = 'volume_deleted'
