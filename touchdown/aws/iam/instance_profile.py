# Copyright 2014 Isotoma Limited
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
from touchdown.core.plan import Plan
from touchdown.core.resource import Resource

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy
from .role import Role


class InstanceProfile(Resource):

    resource_name = 'instance_profile'

    name = argument.String(field='InstanceProfileName')
    path = argument.String(field='Path')
    roles = argument.ResourceList(Role)
    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = InstanceProfile
    service_name = 'iam'
    api_version = '2010-05-08'
    describe_action = 'list_instance_profiles'
    describe_envelope = 'InstanceProfiles'
    describe_filters = {}
    key = 'InstanceProfileName'

    def describe_object_matches(self, instance_profile):
        return instance_profile['InstanceProfileName'] == self.resource.name


class Apply(SimpleApply, Describe):

    create_action = 'create_instance_profile'

    def update_object(self):
        # Make sure all roles in the workspace are linked up to the
        # corresponding InstanceProfile
        remote_roles = [r['RoleName'] for r in self.object.get('Roles', [])]
        for role in self.resource.roles:
            if role.name not in remote_roles:
                yield self.generic_action(
                    'Add role {}'.format(role.name),
                    self.client.add_role_to_instance_profile,
                    InstanceProfileName=self.resource.name,
                    RoleName=role.name,
                )

        # Delete roles that exist on the InstanceProfile at AWS, but arent
        # defined locally
        local_roles = [r.name for r in self.resource.roles]
        for role in remote_roles:
            if role not in local_roles:
                yield self.generic_action(
                    'Remove role {}'.format(role),
                    self.client.remove_role_from_instance_profile,
                    InstanceProfileName=self.resource.name,
                    RoleName=role,
                )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_instance_profile'

    def destroy_object(self):
        remote_roles = [r['RoleName'] for r in self.object.get('Roles', [])]
        for role in remote_roles:
            yield self.generic_action(
                'Remove role {}'.format(role),
                self.client.remove_role_from_instance_profile,
                InstanceProfileName=self.resource.name,
                RoleName=role,
            )

        for change in super(Destroy, self).destroy_object():
            yield change
