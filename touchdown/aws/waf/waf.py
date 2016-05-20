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

from ..common import GenericAction, SimpleApply, SimpleDescribe, SimpleDestroy


class GetChangeTokenAction(GenericAction):

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
        return {"Limit": 20}

    def describe_object_matches(self, d):
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

class WafApply(SimpleApply):

    GenericAction = GetChangeTokenAction

    def update_object(self):
        changes = []
        description = ["Update children of {}".format(self.resouce.name)]

        for local in getattr(self.resource, self.local_container):
            for remote in self.object.get(self.container, []):
                if local.matches(self.runner, remote):
                    break
            else:
                changes.append(serializers.Dict(**{
                    "Action": "INSERT",
                    self.container_member: local.serializer_with_kwargs(),
                }))
                #description.append("Type => {}, Predicate={}, Action=INSERT".format(local.match_type, local.ip_set))

        for remote in self.object.get(self.container, []):
            for local in getattr(self.resource, self.local_container):
                if local.matches(self.runner, remote):
                    break
            else:
                changes.append(serializers.Dict(**{
                    "Action": "DELETE",
                    self.container_member: remote,
                }))
                # TODO: consider doing a call here to a better
                # description for the deleted resource.
                #description.append("Type => {}, Predicate={}, Action=DELETE".format(remote["Type"], remote["DataId"]))

        if changes:
            kwargs = {
                self.key: serializers.Identifier(),
                Updates=serializers.Context(serializers.Const(changes), serializers.List(serializers.SubSerializer())),
            }

            yield self.generic_action(
                description,
                getattr(self.client, self.container_update_action),
                **kwargs,
            )


class WafDestroy(SimpleDestroy):

    """
    Subclasses of this destroy action must set:

        `container` - for example IPSetDescriptors
        `container_member` - for example IPSetDescriptor
    """

    GenericAction = GetChangeTokenAction

    def destroy_object(self):
        changes = []
        description = ["Delete all children from {}".format(self.resource.resource_name)]

        for remote in self.object.get(self.container, []):
            changes.append(serializers.Dict(**{
                "Action": "DELETE",
                self.container_member: remote,
            }))
            #FIXME: Make this nicer
            #description.append("Type => {}, Address={}, Action=DELETE".format(remote["Type"], remote["Value"]))

        if changes:
            kwargs = {
                self.key: serializers.Identifier(),
                "Updates": serializers.Context(serializers.Const(changes), serializers.List(serializers.SubSerializer())),
            }

            yield self.generic_action(
                description,
                getattr(self.client, self.container_update_action),
                **kwargs,
            )

        for obj in super(Destroy, self).destroy_object():
            yield obj
