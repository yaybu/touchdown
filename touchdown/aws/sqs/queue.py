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


class QueueAttributes(Resource):

    delay_seconds = argument.Integer(min=0, max=900, field="DelaySeconds", serializer=serializers.String())
    maximum_message_size = argument.Integer(min=1024, max=262144, field="MaximumMessageSize", serializer=serializers.String())
    message_retention_period = argument.Integer(min=60, max=1209600, field="MessageRetentionPeriod", serializer=serializers.String())
    policy = argument.String(field="Policy")
    receive_message_wait_time_seconds = argument.Integer(min=0, max=20, field="ReceiveMessageWaitTimeSeconds", serializer=serializers.String())
    visibility_timeout = argument.Integer(default=30, min=0, max=43200, field="VisibilityTimeout", serializer=serializers.String())


class Queue(Resource):

    resource_name = "queue"

    name = argument.String(field="QueueName")
    attributes = argument.Resource(QueueAttributes, serializer=serializers.Resource())
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


class Apply(SimpleApply, Describe):

    create_action = "create_queue"
    create_response = "id-only"
    #waiter = "bucket_exists"

    def update_object(self):
        attributes = {}
        if self.resource_id:
            attributes = self.client.get_queue_attributes(
                QueueUrl=self.resource_id,
                AttributeNames=['All'],
            )['Attributes']

        d = DiffSet(self.runner, self.resource.attributes, attributes)
        if d.matches():
            yield self.generic_action(
                ["Updating queue attributes"] + list(d.get_descriptions()),
                self.client.set_queue_attributes,
                QueueUrl=serializers.Identifier(),
                Attributes=serializers.Context(
                    serializers.Const(self.resource.attributes),
                    serializers.Resource(),
                )
            )


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_queue"
    #waiter = "bucket_not_exists"

    def get_destroy_serializer(self):
        return serializers.Dict(
            QueueUrl=serializers.Identifier(),
        )
