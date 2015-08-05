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

from touchdown.core.resource import Resource
from touchdown.core.plan import Plan
from touchdown.core import argument, serializers

from ..account import BaseAccount
from ..common import SimpleDescribe
from . import pipeline


class ActionType(Resource):

    resource_name = "action_type"

    name = argument.String(field="provider")
    version = argument.String(field="version", default=1)
    category = argument.String(
        choices=[
            "Source",
            "Build",
            "Deploy",
            "Test",
            "Invoke"
        ],
        field="category",
    )
    owner = argument.String(
        choices=[
            "AWS",
            "ThirdParty",
        ],
        default="AWS",
        field="owner",
    )

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = ActionType
    service_name = 'codepipeline'
    describe_action = "list_action_types"
    describe_envelope = "actionTypes"
    key = 'id'

    def get_describe_filters(self):
        return {
            "actionOwnerFilter": self.resource.owner,
        }

    def describe_object_matches(self, action):
        if action['id']['provider'] != self.resource.name:
            return False
        if action['id']['version'] != self.resource.version:
            return False
        if action['id']['category'] != self.resource.category:
            return False
        return True


class ActionTypeId(pipeline.ActionTypeId):

    input = ActionType

    def get_serializer(self, runner, **kwargs):
        return serializers.Dict(
            category=self.resource.category,
            provider=self.resource.name,
            version=self.resource.version,
            owner=self.resource.owner,
        )
