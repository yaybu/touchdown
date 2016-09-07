# Copyright 2014-2015 Isotoma Limited
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

from botocore.client import ClientError

from touchdown.core import argument, serializers
from touchdown.core.plan import Plan
from touchdown.interfaces import File, FileNotFound

from ..common import SimpleApply, SimpleDescribe, SimpleDestroy
from .bucket import Bucket


class File(File):

    resource_name = 'file'

    name = argument.String(field='Key')
    contents = argument.String(field='Body')

    acl = argument.String(
        default='private',
        choices=['private', 'public-read', 'public-read-write', 'authenticated-read', 'bucket-owner-read', 'bucket-owner-full-control'],
        field='ACL',
    )

    bucket = argument.Resource(Bucket, field='Bucket')


class Describe(SimpleDescribe, Plan):

    resource = File
    service_name = 's3'
    api_version = '2006-03-01'
    describe_action = 'list_objects'
    describe_envelope = 'Contents'
    key = 'Key'

    def get_describe_filters(self):
        if not self.runner.get_plan(self.resource.bucket).resource_id:
            # If the bucket doesn't exist yet, the file can't. So bail out.
            return

        return {
            'Bucket': self.resource.bucket.name,
        }

    def describe_object_matches(self, obj):
        return obj['Key'] == self.resource.name


class Apply(SimpleApply, Describe):

    create_action = 'put_object'
    create_response = 'not-that-useful'

    def get_actions(self):
        if self.resource.contents:
            return super(Apply, self).get_actions()
        return []


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_object'

    def get_destroy_serializer(self):
        return serializers.Dict(
            Bucket=self.resource.bucket.name,
            Key=self.resource.name,
        )


class FileIo(Plan):

    resource = File
    name = 'fileio'

    def read(self):
        bucket = self.runner.get_service(self.resource.bucket, 'describe')
        if not bucket.describe_object():
            raise FileNotFound('s3://{}/'.format(self.resource.bucket.name))

        describe = self.runner.get_service(self.resource, 'describe')
        try:
            obj = describe.client.get_object(
                Bucket=self.resource.bucket.name,
                Key=self.resource.name,
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFound('s3://{}/{}'.format(
                    self.resource.bucket.name,
                    self.resource.name,
                ))
            raise

        return obj['Body']

    def write(self, contents):
        describe = self.runner.get_service(self.resource, 'describe')
        describe.client.put_object(
            Bucket=self.resource.bucket.name,
            Key=self.resource.name,
            Body=contents,
        )
