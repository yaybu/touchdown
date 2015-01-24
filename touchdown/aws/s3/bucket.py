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

from ..account import Account
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy
from touchdown.core import serializers


class Bucket(Resource):

    resource_name = "bucket"

    name = argument.String(field="Bucket")

    region = argument.String(
        field="CreateBucketConfiguration",
        serializer=serializers.Dict(
            LocationConstraint=serializers.Identity(),
        ),
    )

    account = argument.Resource(Account)


class Describe(SimpleDescribe, Plan):

    resource = Bucket
    service_name = 's3'
    describe_action = "list_buckets"
    describe_list_key = "Buckets"
    key = 'Bucket'

    def describe_object(self):
        for bucket in self.client.list_buckets()['Buckets']:
            if bucket['Name'] == self.resource.name:
                return bucket

    @property
    def resource_id(self):
        if self.object:
            return self.object['Name']
        return None


class Apply(SimpleApply, Describe):

    create_action = "create_bucket"
    create_response = "not-that-useful"
    waiter = "bucket_exists"


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_bucket"
    waiter = "bucket_not_exists"
