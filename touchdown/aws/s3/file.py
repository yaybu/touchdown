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

from touchdown.core.resource import Resource
from touchdown.core.plan import Plan
from touchdown.core import argument

from .bucket import Bucket
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy
from touchdown.core import serializers


class File(Resource):

    resource_name = "file"

    name = argument.String(field="Key")
    contents = argument.String(field="Body")

    acl = argument.String(
        default="private",
        choices=["private", "public-read", "public-read-write", "authenticated-read", "bucket-owner-read", "bucket-owner-full-control"],
        field="ACL",
    )

    bucket = argument.Resource(Bucket, field="Bucket")


class Describe(SimpleDescribe, Plan):

    resource = File
    service_name = 's3'
    describe_action = "list_objects"
    describe_envelope = "Contents"
    key = 'Name'

    def get_describe_filters(self):
        if not self.runner.get_plan(self.resource.bucket).resource_id:
            # If the bucket doesn't exist yet, the file can't. So bail out.
            return

        return {
            "Bucket": self.resource.bucket.name,
        }

    def describe_object_matches(self, obj):
        if obj['Key'] == self.resource.name:
            return True


class Apply(SimpleApply, Describe):

    create_action = "put_object"
    create_response = "not-that-useful"


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_object"

    def get_destroy_serializer(self):
        return serializers.Dict(
            Bucket=self.resource.bucket.name,
            Key=self.resource.name,
        )
