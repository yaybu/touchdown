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

from touchdown.core import argument, serializers
from touchdown.core.adapters import Adapter
from touchdown.core.plan import Plan

from .. import cloudwatch
from ..account import BaseAccount
from ..common import Resource, SimpleApply, SimpleDescribe, SimpleDestroy


class Subscription(Adapter):
    resource_name = 'subscription'


class Topic(Resource):

    resource_name = 'topic'

    arn = argument.Output('TopicArn')

    name = argument.String(field='Name', min=1, max=256, regex='[A-Za-z0-9-_]*')
    notify = argument.ResourceList(Subscription)

    display_name = argument.String(field='DisplayName', group='attributes')
    policy = argument.String(field='Policy', group='attributes')
    delivery_policy = argument.String(field='DeliveryPolicy', group='attributes')

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = Topic
    service_name = 'sns'
    api_version = '2010-03-31'
    describe_action = 'list_topics'
    describe_envelope = 'Topics'
    describe_filters = {}
    key = 'TopicArn'

    def describe_object_matches(self, topic):
        return topic['TopicArn'].endswith(self.resource.name)


class Apply(SimpleApply, Describe):

    create_action = 'create_topic'
    create_response = 'id-only'

    def update_object(self):
        remote_subscriptions = []
        if self.object:
            remote_subscriptions = self.client.list_subscriptions_by_topic(
                TopicArn=self.resource_id,
            )['Subscriptions']

        for local in self.resource.notify:
            for remote in remote_subscriptions:
                if serializers.Resource().diff(self.runner, local, remote).matches():
                    break
            else:
                yield self.generic_action(
                    'Subscribe to {}'.format(local),
                    self.client.subscribe,
                    local.serializer_with_kwargs(
                        TopicArn=self.resource.arn,
                    ),
                )

        for remote in remote_subscriptions:
            for local in self.resource.notify:
                if serializers.Resource().diff(self.runner, local, remote).matches():
                    break
            else:
                yield self.generic_action(
                    'Unsubscribe from protocol {}, endpoint {}'.format(remote['Protocol'], remote['Endpoint']),
                    self.client.unsubscribe,
                    SubscriptionArn=serializers.Const(remote['SubscriptionArn']),
                )

        attributes = {}
        if self.resource_id:
            attributes = self.client.get_topic_attributes(
                TopicArn=self.resource_id,
            )['Attributes']

        d = serializers.Resource(group='attributes').diff(self.runner, self.resource, attributes)
        for field, diff in d.diffs:
            yield self.generic_action(
                'Update {}'.format(diff),
                self.client.set_topic_attributes,
                TopicArn=serializers.Identifier(),
                AttributeName=field.field,
                AttributeValue=diff.local_value,
            )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_topic'


class AlarmDestination(cloudwatch.AlarmDestination):

    ''' Adapts a sns Topic into an AlarmDestination '''

    input = Topic

    @property
    def resource_name(self):
        return self.adapts.resource_name

    def get_serializer(self, runner, **kwargs):
        return self.adapts.arn
