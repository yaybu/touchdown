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

import json

from botocore.exceptions import ClientError

from touchdown.core.resource import Resource
from touchdown.core.plan import Plan
from touchdown.core import argument

from ..account import Account
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy
from touchdown.core import serializers


class CorsRule(Resource):

    resource_name = "cors_rule"

    allowed_headers = argument.List(argument.String(), field="AllowedHeaders")
    allowed_methods = argument.List(argument.String(), field="AllowedMethods")
    allowed_origins = argument.List(argument.String(), field="AllowedOrigins")
    expose_headers = argument.List(argument.String(), field="ExposeHeaders")
    max_age_seconds = argument.Integer(field="MaxAgeSeconds")


class Bucket(Resource):

    resource_name = "bucket"

    name = argument.String(field="Bucket")

    region = argument.String(
        default=lambda instance: instance.account.region,
        field="CreateBucketConfiguration",
        serializer=serializers.Dict(
            LocationConstraint=serializers.Identity(),
        ),
    )

    rules = argument.ResourceList(CorsRule)

    policy = argument.String()

    account = argument.Resource(Account)


class Describe(SimpleDescribe, Plan):

    resource = Bucket
    service_name = 's3'
    describe_action = "list_buckets"
    describe_envelope = "Buckets"
    describe_filters = {}
    key = 'Name'

    def describe_object_matches(self, bucket):
        if bucket['Name'] == self.resource.name:
            # Sometimes the API returns a bucket that doesn't exist!
            try:
                self.client.head_bucket(Bucket=self.resource.name)
                return True
            except:
                return False
        return False

    def describe_object(self):
        bucket = super(Describe, self).describe_object()
        if bucket:
            bucket["LocationConstraint"] = self.client.get_bucket_location(
                Bucket=self.resource.name)['LocationConstraint']
            if bucket['LocationConstraint'] is None:
                bucket['LocationConstraint'] = 'us-east-1'
        return bucket


class Apply(SimpleApply, Describe):

    create_action = "create_bucket"
    create_response = "not-that-useful"
    #waiter = "bucket_exists"

    def update_object(self):
        update_cors = False
        if not self.object and self.resource.rules:
            update_cors = True
        elif self.resource.rules:
            try:
                remote = self.client.get_bucket_cors(Bucket=self.resource.name)["CORSRules"]
            except ClientError as e:
                if e.response['Error']['Code'] != "NoSuchCORSConfiguration":
                    raise
                remote = []
            local = [serializers.Resource().render(self.runner, rule) for rule in self.resource.rules]
            if remote != local:
                update_cors = True

        if update_cors:
            yield self.generic_action(
                "Update CORS rules",
                self.client.put_bucket_cors,
                Bucket=self.resource.name,
                CORSConfiguration=dict(
                    CORSRules=[serializers.Resource().render(self.runner, rule) for rule in self.resource.rules],
                ),
            )

        update_policy = False
        if not self.object and self.resource.policy:
            update_policy = True
        elif self.resource.policy:
            try:
                remote = self.client.get_bucket_policy(Bucket=self.resource.name)["Policy"]
            except ClientError as e:
                if e.response['Error']['Code'] != "NoSuchBucketPolicy":
                    raise
                remote = None

            if self.resource.policy and (remote is None or json.loads(remote) != json.loads(self.resource.policy)):
                update_policy = True

        if update_policy:
            yield self.generic_action(
                "Update bucket policy",
                self.client.put_bucket_policy,
                Bucket=self.resource.name,
                #ContentMD5="",
                Policy=self.resource.policy,
            )


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_bucket"
    #waiter = "bucket_not_exists"

    def get_destroy_serializer(self):
        return serializers.Dict(
            Bucket=self.resource.name,
        )
