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
import re

from botocore.exceptions import ClientError

from touchdown.core import argument, serializers
from touchdown.core.errors import InvalidParameter
from touchdown.core.plan import Plan
from touchdown.core.resource import Resource

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy


class CorsRule(Resource):

    resource_name = 'cors_rule'

    allowed_headers = argument.List(argument.String(), field='AllowedHeaders')
    allowed_methods = argument.List(argument.String(), field='AllowedMethods')
    allowed_origins = argument.List(argument.String(), field='AllowedOrigins')
    expose_headers = argument.List(argument.String(), field='ExposeHeaders')
    max_age_seconds = argument.Integer(field='MaxAgeSeconds')


class Bucket(Resource):

    resource_name = 'bucket'

    arn = argument.Callable(
        lambda instance: 'arn:aws:s3:::{}'.format(instance.name),
    )

    name = argument.String(field='Bucket')

    def clean_name(self, value):
        # This could be enforced with a regex:
        #     ^([a-z0-9]{1})([a-z0-9\-]*[a-z0-9])(\.([a-z0-9]{1})([a-z0-9\-]*[a-z0-9]))*$
        # But we can give better error messages with this
        if value.startswith('.'):
            raise InvalidParameter('Cannot start with a period')
        if value.endswith('.'):
            raise InvalidParameter('Cannot end with a period')
        if value.lower() != value:
            raise InvalidParameter('Cannot have uppercase letters')
        for section in value.split('.'):
            if len(section) == 0:
                raise InvalidParameter('There can be only one period between labels')
            if not re.search(r'^([a-z0-9]{1})([a-z0-9\-]*[a-z0-9])$', value):
                raise InvalidParameter('Value must start and end with a number or letter and can only contain numbers, letters and hyphens')
        return value

    region = argument.String(
        default=lambda instance: instance.account.region,
        field='CreateBucketConfiguration',
        serializer=serializers.Dict(
            LocationConstraint=serializers.Identity(),
        ),
    )

    rules = argument.ResourceList(CorsRule)
    policy = argument.String()

    notify_lambda = argument.ResourceList(
        'touchdown.aws.lambda_.s3.S3LambdaNotification',
        field='LambdaFunctionConfigurations',
        serializer=serializers.List(serializers.Resource()),
        group='notifications',
    )

    accelerate = argument.String(
        choice=['Enabled', 'Suspended'],
        default='Suspended',
        field='Status',
        group='accelerate',
    )

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = Bucket
    service_name = 's3'
    api_version = '2006-03-01'
    describe_action = 'list_buckets'
    describe_envelope = 'Buckets'
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

    def get_location_constraint(self):
        response = self.client.get_bucket_location(Bucket=self.resource.name)
        return response['LocationConstraint'] or 'us-east-1'

    def get_cors_rules(self):
        try:
            return self.client.get_bucket_cors(Bucket=self.resource.name)['CORSRules']
        except ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchCORSConfiguration':
                raise
        return []

    def get_bucket_policy(self):
        try:
            remote = self.client.get_bucket_policy(Bucket=self.resource.name)['Policy']
        except ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchBucketPolicy':
                raise
            return {}
        return json.loads(remote)

    def get_notification_config(self):
        return self.client.get_bucket_notification_configuration(
            Bucket=self.resource.name,
        )

    def get_accelerate_config(self):
        return self.client.get_bucket_accelerate_configuration(
            Bucket=self.resource.name,
        )

    def annotate_object(self, bucket):
        bucket['LocationConstraint'] = self.get_location_constraint()
        bucket['CORSRules'] = self.get_cors_rules()
        bucket['Policy'] = self.get_bucket_policy()
        bucket['NotificationConfiguration'] = self.get_notification_config()
        bucket['AccelerationConfig'] = self.get_accelerate_config()
        return bucket


class Apply(SimpleApply, Describe):

    create_action = 'create_bucket'
    create_response = 'not-that-useful'
    # waiter = 'bucket_exists'

    def update_accelerate_config(self):
        if self.object.get('Status', 'Suspended') != self.resource.accelerate:
            yield self.generic_action(
                'Update acceleration configuration',
                self.client.put_bucket_accelerate_configuration,
                Bucket=self.resource.name,
                AccelerateConfiguration={
                    'Status': self.resource.accelerate,
                }
            )

    def update_notification_config(self):
        local_s = serializers.Default(
            serializers.Resource(group='notifications'),
            serializers.Const({}),
        )
        d = serializers.Resource(group='notifications').diff(
            self.runner,
            self.resource,
            self.object.get('NotificationConfiguration', {}),
        )

        if not d.matches():
            yield self.generic_action(
                ['Update notification configuration'] + list(d.lines()),
                self.client.put_bucket_notification_configuration,
                Bucket=self.resource.name,
                NotificationConfiguration=local_s,
            )

    def update_object(self):
        update_cors = False
        if not self.object and self.resource.rules:
            update_cors = True
        elif self.resource.rules:
            local = [serializers.Resource().render(self.runner, rule) for rule in self.resource.rules]
            if self.object['CORSRules'] != local:
                update_cors = True

        if update_cors:
            yield self.generic_action(
                'Update CORS rules',
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
            remote_policy = self.object['Policy']
            local_policy = json.loads(self.resource.policy)
            if remote_policy != local_policy:
                update_policy = True

        if update_policy:
            yield self.generic_action(
                'Update bucket policy',
                self.client.put_bucket_policy,
                Bucket=self.resource.name,
                Policy=self.resource.policy,
            )

        for action in self.update_notification_config():
            yield action

        for action in self.update_accelerate_config():
            yield action


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_bucket'
    # waiter = 'bucket_not_exists'

    def get_destroy_serializer(self):
        return serializers.Dict(
            Bucket=self.resource.name,
        )

    def destroy_object(self):
        keys = []
        for page in self.client.get_paginator('list_objects').paginate(Bucket=self.resource.name):
            keys.extend(o['Key'] for o in page.get('Contents', []))
        keys.sort()

        for i in range(0, len(keys), 1000):
            chunk = keys[i:i+1000]
            yield self.generic_action(
                'Delete items "{}" through "{}"'.format(chunk[0], chunk[-1]),
                self.client.delete_objects,
                Bucket=self.resource.name,
                Delete={'Objects': [{'Key': k} for k in chunk], 'Quiet': True},
            )

        for action in super(Destroy, self).destroy_object():
            yield action
