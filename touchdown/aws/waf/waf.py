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

import threading

from touchdown.core import serializers
from ..common import GenericAction, SimpleApply, SimpleDescribe, SimpleDestroy


class GetChangeTokenAction(GenericAction):

    '''
    Before every call to a WAF change API first call `get_change_token` and
    inject its response into our API call. *Every* API to create or update a
    WAF resource must have a change token or it will be rejected.

    Wrap all 'action' API calls in a lock so they don't happen concurrently.
    This is because the WAF service does not support concurrent changes
    whatsoever, but touchdown will run in parallel by default.
    '''

    change_token_lock = threading.Lock()

    def get_arguments(self):
        params = super(GetChangeTokenAction, self).get_arguments()
        change_token = self.plan.client.get_change_token()['ChangeToken']
        params['ChangeToken'] = change_token
        return params

    def run(self):
        with self.change_token_lock:
            return super(GetChangeTokenAction, self).run()


class WafDescribe(SimpleDescribe):

    GenericAction = GetChangeTokenAction

    def get_describe_filters(self):
        '''
        The 'Limit' field is mandatory so set it to a sensible default for all
        WAF API's
        '''
        return {'Limit': 20}

    def describe_object_matches(self, d):
        '''
        Perform client side filtering of WAF resources found with the list API.

        There is no server-side filtering at all, and all client-side filtering
        is by comparing self.resource.name against remote['Name'].
        '''
        return self.resource.name == d['Name']

    def annotate_object(self, obj):
        # Need to do a request to get the detailed information for the
        # object - we don't get this for free when doing a list.
        annotate_action = getattr(self.client, self.annotate_action)

        # This will unfurl to be something like::
        #     rule = client.get_rule(RuleId=obj['RuleId'])
        #     obj.update(rule['Rule'])
        obj.update(annotate_action(**{self.key: obj[self.key]})[self.describe_envelope[:-1]])

        return obj

    def get_local_container_field(self):
        return self.resource.meta.fields[self.local_container].argument.list_of

    def get_local_container_items(self):
        return getattr(self.resource, self.local_container, [])

    def describe_local(self, local):
        desc = ['Inserting {}:'.format(local.resource_name)]
        for field in local.meta.iter_fields_in_order():
            if field.name.startswith('_'):
                continue
            if not getattr(field.argument, 'field', None):
                continue
            if not field.present(local):
                continue
            desc.append('    {}: {}'.format(
                field.name,
                getattr(local, field.name, '(unset)'),
            ))
        return desc

    def describe_remote(self, remote):
        '''
        Given a remote object that has no correlation to a local object pretty
        print the remote object (using the touchdown field names)
        '''
        # TODO: consider doing a call here to a better
        # description for the deleted resource - turn its GUID into its name
        field = self.get_local_container_field()
        desc = ['Removing {}:'.format(field.resource_class.resource_name)]
        for field in field.resource_class.meta.iter_fields_in_order():
            if not getattr(field.argument, 'field', None) or field.argument.field not in remote:
                continue
            desc.append('    {}: {}'.format(field.name, remote[field.argument.field]))
        return desc


class WafApply(SimpleApply):

    GenericAction = GetChangeTokenAction

    def update_object(self):
        changes = []
        description = ['Update children of {}'.format(self.resource.name)]

        for local in getattr(self.resource, self.local_container):
            for remote in self.object.get(self.container, []):
                if local.matches(self.runner, remote):
                    break
            else:
                changes.append(serializers.Dict(**{
                    'Action': 'INSERT',
                    self.container_member: local.serializer_with_kwargs(),
                }))
                description.extend(self.describe_local(local))

        for remote in self.object.get(self.container, []):
            for local in getattr(self.resource, self.local_container):
                if local.matches(self.runner, remote):
                    break
            else:
                changes.append(serializers.Dict(**{
                    'Action': 'DELETE',
                    self.container_member: remote,
                }))
                description.extend(self.describe_remote(remote))

        if changes:
            kwargs = {
                self.key: serializers.Identifier(),
                'Updates': serializers.Context(serializers.Const(changes), serializers.List(serializers.SubSerializer())),
            }

            yield self.generic_action(
                description,
                getattr(self.client, self.container_update_action),
                **kwargs
            )


class WafDestroy(SimpleDestroy):

    '''
    Subclasses of this destroy action must set:

        `container` - for example IPSetDescriptors
        `container_member` - for example IPSetDescriptor
    '''

    GenericAction = GetChangeTokenAction

    def destroy_object(self):
        changes = []
        description = ['Delete all children from {}'.format(self.resource.resource_name)]

        for remote in self.object.get(self.container, []):
            changes.append(serializers.Dict(**{
                'Action': 'DELETE',
                self.container_member: remote,
            }))
            description.extend(self.describe_remote(remote))

        if changes:
            kwargs = {
                self.key: serializers.Identifier(),
                'Updates': serializers.Context(serializers.Const(changes), serializers.List(serializers.SubSerializer())),
            }

            yield self.generic_action(
                description,
                getattr(self.client, self.container_update_action),
                **kwargs
            )

        for obj in super(WafDestroy, self).destroy_object():
            yield obj
