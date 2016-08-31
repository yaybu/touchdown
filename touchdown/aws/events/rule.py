# Copyright 2015 Isotoma Limited
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

from touchdown.aws.iam import Role
from touchdown.core import argument, serializers
from touchdown.core.plan import Plan

from ..account import BaseAccount
from ..common import Resource, SimpleApply, SimpleDescribe, SimpleDestroy
from ..lambda_ import Function


class EventTarget(Resource):

    resource_name = 'event_target'

    name = argument.String(field='Id')

    function = argument.Resource(
        Function,
        field='Arn',
        serializer=serializers.Property('FunctionArn'),
    )

    @classmethod
    def clean(cls, obj):
        if isinstance(obj, Function):
            return super(EventTarget, cls).clean({'name': obj.name, 'function': obj})
        return super(EventTarget, cls).clean(obj)


class EventRule(Resource):

    resource_name = 'event_rule'

    arn = argument.Output('Arn')

    name = argument.String(field='Name', min=1, max=140)
    description = argument.String(field='Description', max=256)
    schedule_expression = argument.String(field='ScheduleExpression')
    event_pattern = argument.Dict(
        field='EventPattern',
        serializer=serializers.Json(serializers.Dict()),
        empty_serializer=serializers.Const(''),
    )

    enabled = argument.Boolean(
        field='State',
        serializer=serializers.Boolean(
            on_true='ENABLED',
            on_false='DISABLED',
        ),
    )

    role = argument.Resource(
        Role,
        field='RoleArn',
        serializer=serializers.Property('Arn'),
    )

    targets = argument.ResourceList(
        EventTarget,
    )

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = EventRule
    service_name = 'events'
    api_version = '2015-10-07'
    describe_action = 'list_rules'
    describe_envelope = 'Rules'
    key = 'Name'

    def get_describe_filters(self):
        return {'NamePrefix': self.resource.name}

    def describe_object_matches(self, obj):
        return obj['Name'] == self.resource.name

    def annotate_object(self, obj):
        response = self.client.list_targets_by_rule(
            Rule=self.resource.name,
        )
        obj['Targets'] = response.get('Targets', [])
        return obj


class Apply(SimpleApply, Describe):

    create_action = 'put_rule'
    create_envelope = '@'
    # Create response only gives us the `RuleArn`, and annoyingly
    # describe_object calls the same field `Arn`
    create_response = 'not-that-useful'
    update_action = 'put_rule'

    def update_object(self):
        removals = []
        description = ['Remove old targets']
        for remote in self.object.get('Targets', []):
            for local in self.resource.targets:
                if local.matches(self.runner, remote):
                    break
            else:
                description.append('Remove target: {}'.format(remote['Id']))
                removals.append(remote['Id'])

        if removals:
            yield self.generic_action(
                description,
                self.client.remove_targets,
                Rule=self.resource.name,
                Ids=removals,
            )

        additions = []
        description = ['Add new targets']

        for local in self.resource.targets:
            for remote in self.object.get('Targets', []):
                if local.matches(self.runner, remote):
                    break
            else:
                additions.append(local)
                description.append('Add target: {}'.format(local.name))

        if additions:
            yield self.generic_action(
                description,
                self.client.put_targets,
                Rule=self.resource.name,
                Targets=serializers.Context(
                    serializers.Const(additions),
                    serializers.List(serializers.Resource()),
                ),
            )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_rule'

    def destroy_object(self):
        for remote in self.object.get('Targets', []):
            yield self.generic_action(
                ['Remove old target {}'.format(remote['Id'])],
                self.client.remove_targets,
                Rule=self.resource.name,
                Ids=[remote['Id']],
            )

        for action in super(Destroy, self).destroy_object():
            yield action
