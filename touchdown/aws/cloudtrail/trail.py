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
from touchdown.core.plan import Plan, Present
from touchdown.core.resource import Resource

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy
from ..iam import Role
from ..logs import LogGroup
from ..s3 import Bucket
from ..sns import Topic


class Trail(Resource):

    resource_name = 'trail'

    name = argument.String(field='Name')
    logging = argument.Boolean(default=True)
    bucket = argument.Resource(Bucket, field='S3BucketName')
    bucket_prefix = argument.String(field='S3KeyPrefix')
    topic = argument.Resource(Topic, field='SnsTopicName')
    include_global = argument.Boolean(field='IncludeGlobalServiceEvents')
    cwlogs_group = argument.Resource(LogGroup, field='CloudWatchLogsLogGroupArn', serializer=serializers.Property('arn'))
    cwlogs_role = argument.Resource(Role, field='CloudWatchLogsRoleArn', serializer=serializers.Property('Arn'))

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = Trail
    service_name = 'cloudtrail'
    api_version = '2013-11-01'
    describe_action = 'describe_trails'
    describe_envelope = 'trailList'
    key = 'Name'

    def get_describe_filters(self):
        return {
            'trailNameList': [self.resource.name],
        }


class Apply(SimpleApply, Describe):

    create_action = 'create_trail'
    update_action = 'update_trail'
    create_response = 'not-that-useful'

    retryable = {
        'InvalidCloudWatchLogsRoleArnException': [
            'Access denied. Check the trust relationships for your role.',
        ],
    }

    signature = [
        Present('name'),
        Present('bucket'),
    ]


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_trail'

    def get_destroy_serializer(self):
        return serializers.Dict(
            Name=self.resource.name,
        )
