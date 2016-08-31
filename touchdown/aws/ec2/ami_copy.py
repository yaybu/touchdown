# Copyright 2014-2015 Isotoma Limited
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

from touchdown.core import argument, serializers
from touchdown.core.plan import Plan, Present
from touchdown.core.resource import Resource

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy, TagsMixin
from .ami import Image


class ImageCopy(Resource):

    resource_name = 'image_copy'
    immutable_tags = True

    name = argument.String(min=3, max=128, field='Name')
    description = argument.String(field='Description')
    source = argument.Resource(Image, field='SourceImageId')

    launch_permissions = argument.List()
    tags = argument.Dict()

    account = argument.Resource(BaseAccount)

    extra_serializers = {
        'SourceRegion': serializers.Expression(lambda runner, obj: obj.source.account.region),
    }

    def __str__(self):
        return 'image_copy "{}" (copy from {} to {})'.format(self.name, self.source.account.region, self.account.region)


class Describe(SimpleDescribe, Plan):

    resource = ImageCopy
    service_name = 'ec2'
    api_version = '2015-10-01'
    describe_action = 'describe_images'
    describe_envelope = 'Images'
    key = 'ImageId'

    def get_describe_filters(self):
        return {'Filters': [{'Name': 'name', 'Values': [self.resource.name]}]}


class Apply(TagsMixin, SimpleApply, Describe):

    create_action = 'copy_image'
    create_response = 'id-only'
    waiter = 'image_available'

    signature = (
        Present('name'),
    )

    def update_object(self):
        for change in super(Apply, self).update_object():
            yield change

        description = ['Update who can launch this image']

        remote_userids = []
        if self.object:
            results = self.client.describe_image_attribute(
                ImageId=self.object['ImageId'],
                Attribute='launchPermission',
            ).get('LaunchPermissions', [])
            remote_userids = [r['UserId'] for r in results]

        add = []
        for userid in self.resource.launch_permissions:
            if userid not in remote_userids:
                description.append('Add launch permission for "{}"'.format(userid))
                add.append({'UserId': userid})

        remove = []
        for userid in remote_userids:
            if userid not in self.resource.launch_permissions:
                description.append('Remove launch permission for "{}"'.format(userid))
                remove.append({'UserId': userid})

        if add or remove:
            yield self.generic_action(
                description,
                self.client.modify_image_attribute,
                ImageId=serializers.Identifier(),
                Attribute='launchPermission',
                LaunchPermission=dict(
                    Add=add,
                    Remove=remove,
                ),
            )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'deregister_image'
