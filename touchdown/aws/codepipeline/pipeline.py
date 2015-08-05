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
from touchdown.core.plan import Plan, Present
from touchdown.core import argument, serializers
from touchdown.core.adapters import Adapter

from ..account import BaseAccount
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy
from ..iam import Role
from ..s3 import Bucket


class ActionTypeId(Adapter):
    resource_name = "action_type"


class Action(Resource):

    resource_name = "pipeline_action"

    name = argument.String(field="name")
    role = argument.Resource(Role, field="roleArn")
    action_type = argument.Resource(ActionTypeId, field="actionTypeId")

    inputs = argument.List(
        argument.String(),
        field="inputArtifacts",
        serializer=serializers.List(
            serializers.Dict(
                name=serializers.String(),
            ),
        ),
    )
    outputs = argument.List(
        argument.String(),
        field="outputArtifacts",
        serializer=serializers.List(
            serializers.Dict(
                name=serializers.String(),
            ),
        ),
    )
    configuration = argument.Dict(field="configuration")
    run_order = argument.Integer(min=1, max=99, default=1, field="runOrder")


class Stage(Resource):

    resource_name = "pipeline_stage"

    name = argument.String(min=1, max=100, field="name")
    blockers = argument.List(
        argument.String(),
        field="blockers",
        serializer=serializers.List(
            serializers.Dict(
                type="Schedule",
                name=serializers.String(),
            ),
        ),
    )
    actions = argument.ResourceList(
        Action,
        field="actions",
        serializer=serializers.List(serializers.Resource()),
    )


class Pipeline(Resource):

    resource_name = "pipeline"

    name = argument.String(field="name")
    role = argument.Resource(Role, field="roleArn")

    bucket = argument.Resource(
        Bucket,
        field="artifactStore",
        serializer=serializers.Dict(
            type="S3",
            location=serializers.Identifier(),
        ),
    )

    stages = argument.ResourceList(
        Stage,
        min=2,
        field="stages",
        serializer=serializers.List(serializers.Resource()),
    )

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = Pipeline
    service_name = 'codepipeline'
    describe_action = "get_pipeline"
    describe_envelope = "pipeline"
    key = 'name'

    def get_describe_filters(self):
        return {
            "name": self.resource.name,
        }


class Apply(SimpleApply, Describe):

    create_action = "create_pipeline"

    signature = (
        Present("name"),
        Present("role"),
        Present("bucket"),
        Present("stages"),
    )

    def get_create_serializer(self):
        return serializers.Dict(
            pipeline=serializers.Resource(),
        )


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_pipeline"
