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
from touchdown.core.resource import Resource

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy


class EventRule(Resource):

    resource_name = "event_rule"

    arn = argument.Output("RuleArn")

    name = argument.String(field="Name", min=1, max=140)
    description = argument.String(field="Description", max=256)
    schedule_expression = argument.String(field="ScheduleExpression")
    event_pattern = argument.Dict(
        field="EventPattern",
        serializer=serializers.Json(),
    )

    enabled = argument.Boolean(
        field="State",
        serializer=serializers.Boolean(
            on_true="ENABLED",
            on_false="DISABLED",
        ),
    )

    role = argument.Resource(
        Role,
        field="RoleArn",
        serializer=serializers.Property("Arn"),
    )

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = EventRule
    service_name = 'events'
    describe_action = "list_rules"
    describe_envelope = "Rules"
    key = 'Name'


class Apply(SimpleApply, Describe):

    create_action = "put_rule"
    create_envelope = "@"
    update_action = "put_rule"


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_rule"
