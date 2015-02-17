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

from touchdown.core.plan import Plan
from touchdown.core import argument

from ..account import Account
from ..common import Resource, SimpleDescribe, SimpleApply, SimpleDestroy
from touchdown.core import serializers
from touchdown.core.diff import DiffSet

from .. import sns


class Queue(Resource):

    resource_name = "queue"

    name = argument.String(field="QueueName")

    delay_seconds = argument.Integer(min=0, max=900, field="DelaySeconds", serializer=serializers.String(), group="attributes")
    maximum_message_size = argument.Integer(min=1024, max=262144, field="MaximumMessageSize", serializer=serializers.String(), group="attributes")
    message_retention_period = argument.Integer(min=60, max=1209600, field="MessageRetentionPeriod", serializer=serializers.String(), group="attributes")
    policy = argument.String(field="Policy", group="attributes")
    receive_message_wait_time_seconds = argument.Integer(min=0, max=20, field="ReceiveMessageWaitTimeSeconds", serializer=serializers.String(), group="attributes")
    visibility_timeout = argument.Integer(default=30, min=0, max=43200, field="VisibilityTimeout", serializer=serializers.String(), group="attributes")

    account = argument.Resource(Account)


class Describe(SimpleDescribe, Plan):

    resource = Queue
    service_name = 'sqs'
    describe_action = 'get_queue_url'
    describe_envelope = "{QueueUrl: QueueUrl}"
    describe_notfound_exception = "AWS.SimpleQueueService.NonExistentQueue"
    key = "QueueUrl"

    def get_describe_filters(self):
        return {"QueueName": self.resource.name}

    def describe_object(self):
        object = super(Describe, self).describe_object()
        if object:
            object.update(self.client.get_queue_attributes(
                QueueUrl=object['QueueUrl'],
                AttributeNames=['All'],
            )['Attributes'])
        return object


class Apply(SimpleApply, Describe):

    create_action = "create_queue"
    create_response = "id-only"
    #waiter = "bucket_exists"

    def update_object(self):
        d = DiffSet(self.runner, self.resource, self.object, group="attributes")
        if not d.matches():
            yield self.generic_action(
                ["Updating queue attributes"] + list(d.get_descriptions()),
                self.client.set_queue_attributes,
                QueueUrl=serializers.Identifier(),
                Attributes=serializers.Resource(group="attributes")
            )


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_queue"
    #waiter = "bucket_not_exists"

    def get_destroy_serializer(self):
        return serializers.Dict(
            QueueUrl=serializers.Identifier(),
        )


class Subscription(sns.Subscription):

    """ Adapts a Queue into a Subscription """

    input = Queue

    def get_serializer(self, runner, **kwargs):
        return serializers.Dict(
            Protocol=serializers.Const("sqs"),
            Endpoint=serializers.Context(
                serializers.Const(self.adapts),
                serializers.Property("QueueArn"),
            ),
            TopicArn=kwargs['TopicArn'],
        )
