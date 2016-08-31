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

from touchdown.core import serializers

from .common import SimpleApply, SimpleDescribe, SimpleDestroy


class ReplacementDescribe(SimpleDescribe):

    name = 'describe'
    biggest_serial = 0

    def name_for_remote(self, obj):
        return obj[self.key]

    def is_possible_object(self, obj):
        name = self.name_for_remote(obj)
        if name == self.resource.name:
            return True
        if name.startswith(self.resource.name + '.'):
            return True

    def get_possible_objects(self):
        for obj in super(ReplacementDescribe, self).get_possible_objects():
            if self.is_possible_object(obj):
                yield obj

    def describe_object_matches(self, obj):
        try:
            serial = self.name_for_remote(obj).rsplit('.', 1)[1]
            self.biggest_serial = max(int(serial), self.biggest_serial)
        except (IndexError, TypeError, ValueError):
            pass

        return self.resource.diff(self.runner, obj).matches()


class ReplacementApply(SimpleApply):

    name = 'apply'

    def get_create_name(self):
        return '{}.{}'.format(
            self.resource.name,
            self.biggest_serial + 1,
        )

    def get_create_serializer(self):
        return serializers.Resource(**{
            self.key: self.get_create_name(),
        })

    def is_stale(self, obj):
        # Don't try and delete self!!!
        if obj[self.key] == self.resource_id:
            return False
        return True

    def prepare_to_create(self):
        '''
        Find all versions of the named resource and if they are stale terminate them

        What it means to be stale varies between resources so this is delegated to `self.is_stale`.
        '''
        # TODO: There is a considerable amount of overlap with the destroy action here...
        for obj in self.get_possible_objects():
            if not self.is_stale(obj):
                continue

            yield self.generic_action(
                'Destroy stale {} {}'.format(self.resource.resource_name, obj[self.key]),
                getattr(self.client, self.destroy_action),
                serializers.Dict(**{self.key: obj[self.key]}),
            )


class ReplacementDestroy(SimpleDestroy):

    name = 'destroy'

    def get_destroy_serializer(self, resource_id):
        return serializers.Dict(**{self.key: resource_id})

    def get_actions(self):
        self.object = self.describe_object()
        for obj in self.get_possible_objects():
            yield self.generic_action(
                'Destroy {} {}'.format(self.resource.resource_name, obj[self.key]),
                getattr(self.client, self.destroy_action),
                self.get_destroy_serializer(obj[self.key]),
            )
