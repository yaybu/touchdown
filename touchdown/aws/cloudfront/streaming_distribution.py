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

import uuid

from touchdown.core import argument, serializers
from touchdown.core.plan import Plan, Present
from touchdown.core.resource import Resource

from .. import route53
from ..account import BaseAccount
from ..common import (
    RefreshMetadata,
    SimpleApply,
    SimpleDescribe,
    SimpleDestroy,
    Waiter,
)
from ..s3 import Bucket
from .common import CloudFrontList


class StreamingLoggingConfig(Resource):

    resource_name = 'streaming_logging_config'
    dot_ignore = True

    enabled = argument.Boolean(field='Enabled', default=False)
    bucket = argument.Resource(Bucket, field='Bucket', serializer=serializers.Default(default=None), default='')
    prefix = argument.String(field='Prefix', default='')


class StreamingDistribution(Resource):

    resource_name = 'streaming_distribution'

    extra_serializers = {
        'CallerReference': serializers.Expression(
            lambda runner, object: runner.get_plan(object).object.get('StreamingDistributionConfig', {}).get('CallerReference', str(uuid.uuid4()))
        ),
        'Aliases': CloudFrontList(serializers.Chain(
            serializers.Argument('cname'),
            serializers.Argument('aliases'),
        )),
        'TrustedSigners': serializers.Const({
            'Enabled': False,
            'Quantity': 0,
        }),
        'S3Origin': serializers.Resource(group='s3origin'),
    }

    name = argument.String()
    cname = argument.String(default=lambda instance: instance.name, serializer=serializers.ListOfOne(maybe_empty=True))
    comment = argument.String(field='Comment', default=lambda instance: instance.name)
    aliases = argument.List()
    enabled = argument.Boolean(default=True, field='Enabled')

    bucket = argument.Resource(
        Bucket,
        field='DomainName',
        serializer=serializers.Format('{0}.s3.amazonaws.com', serializers.Identifier()),
        group='s3origin'
    )
    origin_access_identity = argument.String(default='', field='OriginAccessIdentity', group='s3origin')
    logging = argument.Resource(
        StreamingLoggingConfig,
        default=lambda instance: dict(enabled=False),
        field='Logging',
        serializer=serializers.Resource(),
    )
    price_class = argument.String(
        default='PriceClass_100',
        choices=['PriceClass_100', 'PriceClass_200', 'PriceClass_All'],
        field='PriceClass',
    )

    account = argument.Resource(BaseAccount)


class StreamingDistributionWaiter(Waiter):

    def get_waiter_filters(self):
        return {'Id': self.plan.object['Id']}


class Describe(SimpleDescribe, Plan):

    resource = StreamingDistribution
    service_name = 'cloudfront'
    api_version = '2016-01-28'
    describe_filters = {}
    describe_action = 'list_streaming_distributions'
    describe_envelope = 'StreamingDistributionList.Items'
    key = 'Id'

    def get_waiter(self, description, waiter, eventual_consistency_threshold=1):
        return StreamingDistributionWaiter(self, description, waiter, eventual_consistency_threshold)

    def describe_object_matches(self, d):
        return self.resource.name == d['Comment'] or self.resource.name in d['Aliases'].get('Items', [])

    def annotate_object(self, obj):
        result = self.client.get_streaming_distribution(Id=obj['Id'])
        distribution = {
            'ETag': result['ETag'],
            'Id': obj['Id'],
        }
        distribution.update(result['StreamingDistribution'])
        return distribution


class Apply(SimpleApply, Describe):

    create_action = 'create_streaming_distribution'
    create_response = 'not-that-useful'
    waiter = 'streaming_distribution_deployed'

    signature = (
        Present('name'),
        Present('bucket'),
    )

    def get_create_serializer(self):
        return serializers.Dict(
            StreamingDistributionConfig=serializers.Resource(),
        )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_streaming_distribution'

    def get_destroy_serializer(self):
        return serializers.Dict(
            Id=self.resource_id,
            IfMatch=serializers.Property('ETag'),
        )

    def destroy_object(self):
        if self.object['StreamingDistributionConfig'].get('Enabled', False):
            yield self.generic_action(
                'Disable streaming distribution',
                self.client.update_streaming_distribution,
                Id=self.object['Id'],
                IfMatch=self.object['ETag'],
                StreamingDistributionConfig=serializers.Resource(
                    Enabled=False,
                ),
            )

            yield self.get_waiter(
                ['Waiting for streaming distribution to enter disabled state'],
                'streaming_distribution_deployed',
            )

            yield RefreshMetadata(self)

        for change in super(Destroy, self).destroy_object():
            yield change


class AliasTarget(route53.AliasTarget):

    ''' Adapts a StreamingDistribution into a AliasTarget '''

    streaming_distribution = argument.Resource(
        StreamingDistribution,
        field='DNSName',
        serializer=serializers.Context(
            serializers.Property('DomainName'),
            serializers.Expression(lambda r, o: route53._normalize(o)),
        ),
    )

    hosted_zone_id = argument.String(
        default='Z2FDTNDATAQYW2',
        field='HostedZoneId',
    )

    evaluate_target_health = argument.Boolean(
        default=False,
        field='EvaluateTargetHealth',
    )
