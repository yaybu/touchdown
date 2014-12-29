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

import uuid

from touchdown.core.resource import Resource
from touchdown.core.target import Target
from touchdown.core.action import Action
from touchdown.core import argument, errors

from ..account import AWS
from ..common import SimpleApply


class Bucket(Resource):

    resource_name = "bucket"

    name = argument.String()
    comment = argument.String()
    region = argument.String(default=lambda instance: instance.account.region)
    account = argument.Resource(AWS)


class AddBucket(Action):

    @property
    def description(self):
        yield "Add bucket '{}'".format(self.resource.name)

    def run(self):
        #FIXME: Add: ACL, GrantFullControl, GrantRead, GrantReadACP, etc
        self.target.client.create_bucket(
            Bucket=self.resource.name,
            CreateBucketConfiguration=dict(
                LocationConstraint=self.resource.region,
            ),
        )


class Apply(SimpleApply, Target):

    resource = Bucket
    add_action = AddBucket

    def get_object(self, runner):
        account = runner.get_target(self.resource.account)
        self.client = account.get_client('s3')

        for bucket in self.client.list_buckets()['Buckets']:
            if bucket['Name'] == self.resource.name:
                return bucket
