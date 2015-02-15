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


class TopicAttributes(Resource):

    display_name = argument.String(field="DisplayName")
    policy = argument.String(field="Policy")
    delivery_policy = argument.String(field="DeliveryPolicy")


class Topic(Resource):

    resource_name = "topic"

    name = argument.String(field="Name", min=1, max=256, regex='[A-Za-z0-9-_]*')
    attributes = argument.Resource(TopicAttributes)
    account = argument.Resource(Account)


class Describe(SimpleDescribe, Plan):

    resource = Topic
    service_name = 'sns'
    describe_action = "list_topics"
    describe_envelope = "Topics"
    key = 'TopicArn'

    def describe_object_matches(self, topic):
        return topic['TopicArn'].endswith(self.resource.name)


class Apply(SimpleApply, Describe):

    create_action = "create_topic"
    create_response = "id-only"

    def update_object(self):
        attributes = {}
        if self.resource_id:
            attributes = self.client.get_topic_attributes(
                TopicArn=self.resource_id,
            )['Attributes']

        d = DiffSet(self.runner, self.resource.attributes, attributes)
        for diff in d.get_changes():
            yield self.generic_action(
                "Update {}".format(diff),
                self.client.set_topic_attributes,
                TopicArn=serializers.Identifier(),
                AttributeName=diff.remote_name,
                AttributeValue=diff.local_value,
            )


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_topic"
