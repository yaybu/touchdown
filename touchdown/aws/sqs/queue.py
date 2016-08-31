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
from touchdown.core.plan import Plan

from .. import cloudwatch, sns
from ..account import BaseAccount
from ..common import Resource, SimpleApply, SimpleDescribe, SimpleDestroy


class Queue(Resource):

    resource_name = 'queue'

    name = argument.String(field='QueueName')

    delay_seconds = argument.Integer(min=0, max=900, field='DelaySeconds', serializer=serializers.String(), group='attributes')
    maximum_message_size = argument.Integer(
        min=1024,
        max=262144,
        field='MaximumMessageSize',
        serializer=serializers.String(),
        group='attributes'
    )
    message_retention_period = argument.Integer(
        min=60,
        max=1209600,
        field='MessageRetentionPeriod',
        serializer=serializers.String(),
        group='attributes'
    )
    policy = argument.String(field='Policy', group='attributes')
    receive_message_wait_time_seconds = argument.Integer(
        min=0,
        max=20,
        field='ReceiveMessageWaitTimeSeconds',
        serializer=serializers.String(),
        group='attributes'
    )
    visibility_timeout = argument.Integer(
        default=30,
        min=0,
        max=43200,
        field='VisibilityTimeout',
        serializer=serializers.String(),
        group='attributes'
    )

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = Queue
    service_name = 'sqs'
    api_version = '2012-11-05'
    describe_action = 'get_queue_url'
    describe_envelope = '[@]'
    describe_notfound_exception = 'AWS.SimpleQueueService.NonExistentQueue'
    key = 'QueueUrl'

    def get_describe_filters(self):
        return {'QueueName': self.resource.name}

    def annotate_object(self, queue):
        queue.update(self.client.get_queue_attributes(
            QueueUrl=queue['QueueUrl'],
            AttributeNames=['All'],
        )['Attributes'])
        return queue


class Apply(SimpleApply, Describe):

    create_action = 'create_queue'
    create_response = 'id-only'

    def update_object(self):
        d = serializers.Resource(group='attributes').diff(self.runner, self.resource, self.object)
        if not d.matches():
            yield self.generic_action(
                ['Updating queue attributes'] + list(d.lines()),
                self.client.set_queue_attributes,
                QueueUrl=serializers.Identifier(),
                Attributes=serializers.Resource(group='attributes')
            )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_queue'
    # waiter = 'bucket_not_exists'

    def get_destroy_serializer(self):
        return serializers.Dict(
            QueueUrl=serializers.Identifier(),
        )


class Subscription(sns.Subscription):

    ''' Adapts a Queue into a Subscription '''

    input = Queue

    def get_serializer(self, runner, **kwargs):
        return serializers.Dict(
            Protocol=serializers.Const('sqs'),
            Endpoint=self.adapts.get_property('QueueArn'),
            TopicArn=kwargs['TopicArn'],
        )


class AlarmDestination(cloudwatch.AlarmDestination):

    ''' Adapts a Queue into an AlarmDestination '''

    input = Queue

    def get_serializer(self, runner, **kwargs):
        return self.adapts.get_property('QueueArn')
