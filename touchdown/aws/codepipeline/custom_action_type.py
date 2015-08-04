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

import time

from touchdown.core.resource import Resource
from touchdown.core.plan import Plan, Present
from touchdown.core import argument, serializers

from ..account import BaseAccount
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy
from .. import common


class ArtifactDetail(Resource):

    resource_name = "custom_action_type_artifacts"

    min = argument.Integer(field="minimumCount", default=0)
    max = argument.Integer(field="maximumCount", default=0)


class Property(Resource):

    resource_name = "custom_action_type_property"

    name = argument.String(field="name")
    description = argument.String(field="description")
    property_type = argument.String(
        choices=[
            "String",
            "Number",
            "Boolean",
        ],
        field="type"
    )
    required = argument.Boolean(field="required")
    key = argument.Boolean(field="required")
    secret = argument.Boolean(field="secret")
    queryable = argument.Boolean(field="queryable")


class CustomActionType(Resource):

    resource_name = "custom_action_type"

    name = argument.String(field="provider")
    version = argument.String(field="version")
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

    properties = argument.ResourceList(Property, field="configurationProperties")

    inputs = argument.Resource(
        ArtifactDetail,
        default=lambda instance: {},
        field="inputArtifactDetails",
        serializer=serializers.Resource(),
    )

    outputs = argument.Resource(
        ArtifactDetail,
        default=lambda instance: {},
        field="outputArtifactDetails",
        serializer=serializers.Resource()
    )

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = CustomActionType
    service_name = 'codepipeline'
    describe_action = "list_action_types"
    describe_envelope = "actionTypes"
    key = 'id'

    def get_describe_filters(self):
        return {
            "actionOwnerFilter": "Custom",
        }

    def describe_object_matches(self, action):
        if action['id']['provider'] != self.resource.name:
            return False
        if action['id']['version'] != self.resource.version:
            return False
        if action['id']['category'] != self.resource.category:
            return False
        return True


class Apply(SimpleApply, Describe):

    create_action = "create_custom_action_type"
    create_response = "not-that-useful"

    signature = [
        Present("category"),
        Present("name"),
        Present("version"),
    ]


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_custom_action_type"

    def get_destroy_serializer(self):
        return serializers.Dict(
            category=self.resource.category,
            provider=self.resource.name,
            version=self.resource.version,
        )


class ProcessPipelineJobs(common.SimplePlan):

    name = "process_pipeline_jobs"
    resource = CustomActionType
    service_name = "codepipeline"

    def dispatch_job(job):
        pass

    def process_job(self, job):
        self.client.acknowledge_job(
            id=job['id'],
            nonce=job['nonce'],
        )

        try:
            self.dispatch_job(job)
        except Exception as e:
            self.client.put_job_failure_result(
                jobId=job['id'],
                failureDetails={
                    "type": "JobFailed",
                    "message": str(e),
                }
            )
            raise

        self.client.put_job_success_result(
            jobId=job['id'],
        )

    def process_jobs_once(self):
        result = self.client.poll_for_jobs(actionTypeId={
            "category": self.resource.category,
            "owner": "Custom",
            "provider": self.resource.name,
            "version": self.resource.version,
        })
        for job in result['jobs']:
            try:
                self.process_job(job)
            except Exception as e:
                print(e)

    def process_jobs(self):
        while True:
            self.process_jobs_once()
            time.sleep(60)
