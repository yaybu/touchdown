# Copyright 2014 Isotoma Limited
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
from touchdown.core import argument

from ..account import Account
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy

from ..s3 import Bucket
from ..iam import Role


class Pipeline(Resource):

    resource_name = "pipeline"

    name = argument.String(field="Name")
    input_bucket = argument.Resource(Bucket, field="InputBucket")
    output_bucket = argument.Resource(Bucket, field="OutputBucket")
    role = argument.Resource(Role, field="Role")
    # key = argument.Resource(KmsKey, field="AwsKmsKeyArn")
    # notifications = argument.Resource(Topic, field="Notifications")
    content_config = argument.Dict(field="ContentConfig")
    thumbnail_config = argument.Dict(field="ThumbnailConfig")
    account = argument.Resource(Account)


class Describe(SimpleDescribe, Plan):

    resource = Pipeline
    service_name = 'elastictranscoder'
    describe_action = "list_pipelines"
    describe_list_key = "Pipelines"
    key = 'Id'

    def describe_object(self):
        for pipeline in self.client.list_buckets()['Pipelines']:
            if pipeline['Name'] == self.resource.name:
                return pipeline


class Apply(SimpleApply, Plan):

    create_action = "create_pipeline"
    update_action = "update_pipeline"


class Destroy(SimpleDestroy, Plan):

    destroy_action = "delete_pipeline"
