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
from touchdown.core.resource import Resource, Meta

from .. import route53
from ..account import BaseAccount
from ..common import (
    RefreshMetadata,
    SimpleApply,
    SimpleDescribe,
    SimpleDestroy,
    Waiter,
)
from ..elb import LoadBalancer
from ..iam import ServerCertificate
from ..s3 import Bucket
from ..waf import WebACL
from .common import CloudFrontList, CloudFrontResourceList, S3Origin

class CustomOrigin(Resource):

    resource_name = 'custom_origin'
    dot_ignore = True

    extra_serializers = {
        'CustomHeaders': serializers.Dict(
            Quantity=0,
            Items=[],
        ),
    }

    name = argument.String(field='Id')
    domain_name = argument.String(field='DomainName')
    origin_path = argument.String(default='', field='OriginPath')

    http_port = argument.Integer(default=80, field='HTTPPort', group='custom-origin-config')
    https_port = argument.Integer(default=443, field='HTTPSPort', group='custom-origin-config')
    protocol = argument.String(
        choices=['http-only', 'match-viewer'],
        default='match-viewer',
        field='OriginProtocolPolicy',
        group='custom-origin-config',
    )
    ssl_policy = argument.List(
        choices=['SSLv3', 'TLSv1', 'TLSv1.1', 'TLSv1.2', 'TLSv1.1_2016'],
        default=['SSLv3', 'TLSv1'],
        field='OriginSslProtocols',
        group='custom-origin-config',
        serializer=CloudFrontList(serializers.List()),
    )

    _custom_origin_config = argument.Serializer(
        serializer=serializers.Resource(group='custom-origin-config'),
        field='CustomOriginConfig',
    )


class LoadBalancerOrigin(Resource):

    resource_name = 'elb_origin'
    dot_ignore = True

    extra_serializers = {
        'CustomHeaders': serializers.Dict(
            Quantity=0,
            Items=[],
        ),
    }

    name = argument.String(field='Id')
    load_balancer = argument.Resource(
        LoadBalancer,
        field='DomainName',
        serializer=serializers.Property('DNSName'),
    )
    origin_path = argument.String(default='', field='OriginPath')

    http_port = argument.Integer(default=80, field='HTTPPort', group='custom-origin-config')
    https_port = argument.Integer(default=443, field='HTTPSPort', group='custom-origin-config')
    protocol = argument.String(
        choices=['http-only', 'match-viewer'],
        default='match-viewer',
        field='OriginProtocolPolicy',
        group='custom-origin-config',
    )
    ssl_policy = argument.List(
        choices=['SSLv3', 'TLSv1', 'TLSv1.1', 'TLSv1.2', 'TLSv1.1_2016'],
        default=['SSLv3', 'TLSv1'],
        field='OriginSslProtocols',
        group='custom-origin-config',
        serializer=CloudFrontList(serializers.List()),
    )

    _custom_origin_config = argument.Serializer(
        serializer=serializers.Resource(group='custom-origin-config'),
        field='CustomOriginConfig',
    )


class DefaultCacheBehavior(Resource):

    resource_name = 'default_cache_behaviour'
    dot_ignore = True

    extra_serializers = {
        # TrustedSigners are not supported yet, so include stub in serialized form
        'TrustedSigners': serializers.Const({
            'Enabled': False,
            'Quantity': 0,
        }),
        'AllowedMethods': CloudFrontList(
            inner=serializers.Argument('allowed_methods'),
            CachedMethods=serializers.Argument('cached_methods'),
        ),
        'ForwardedValues': serializers.Resource(
            group='forwarded-values',
            Cookies=serializers.Resource(
                group='cookies',
                Forward=serializers.Expression(
                    lambda r, o: 'all' if o.forward_cookies == ['*'] else 'none' if len(o.forward_cookies) == 0 else 'whitelist'
                ),
            )
        )
    }

    target_origin = argument.String(field='TargetOriginId')

    forward_query_string = argument.Boolean(default=True, field='QueryString', group='forwarded-values')
    forward_headers = argument.List(field='Headers', serializer=CloudFrontList(serializers.List()), group='forwarded-values')
    forward_cookies = argument.List(field='WhitelistedNames', serializer=CloudFrontList(
        serializers.Expression(lambda r, o: [] if o == ['*'] else o)), group='cookies'
    )

    allowed_methods = argument.List(default=lambda x: ['GET', 'HEAD'],)
    cached_methods = argument.List(default=lambda x: ['GET', 'HEAD'], serializer=CloudFrontList())

    default_ttl = argument.Integer(default=86400, field='DefaultTTL')
    min_ttl = argument.Integer(default=0, field='MinTTL')
    max_ttl = argument.Integer(default=31536000, field='MaxTTL')
    compress = argument.Boolean(default=False, field='Compress')

    viewer_protocol_policy = argument.String(
        choices=['allow-all', 'https-only', 'redirect-to-https'],
        default='allow-all',
        field='ViewerProtocolPolicy'
    )
    smooth_streaming = argument.Boolean(default=False, field='SmoothStreaming')


class CacheBehavior(DefaultCacheBehavior):

    resource_name = 'cache_behaviour'
    path_pattern = argument.String(field='PathPattern')


class ErrorResponse(Resource):

    resource_name = 'error_response'
    dot_ignore = True

    error_code = argument.Integer(field='ErrorCode', choices=[
        '400', '403', '404', '405', '414',
        '500', '501', '502', '503', '504',
    ])
    response_page_path = argument.String(field='ResponsePagePath')
    response_code = argument.String(field='ResponseCode', choices=[
        '200',
        '400', '403', '404', '405', '414',
        '500', '501', '502', '503', '504',
    ])
    min_ttl = argument.Integer(field='ErrorCachingMinTTL')


class LoggingConfig(Resource):

    resource_name = 'logging_config'
    dot_ignore = True

    enabled = argument.Boolean(field='Enabled', default=False)
    include_cookies = argument.Boolean(field='IncludeCookies', default=False)
    bucket = argument.Resource(
        Bucket,
        field='Bucket',
        serializer=serializers.Append('.s3.amazonaws.com', serializers.Property('Name')),
        empty_serializer=serializers.Const(''),
    )
    prefix = argument.String(field='Prefix', default='')


class Distribution(Resource):

    resource_name = 'distribution'

    extra_serializers = {
        'CallerReference': serializers.Expression(
            lambda runner, object: runner.get_plan(object).object.get('CallerReference', str(uuid.uuid4()))
        ),
        'Aliases': CloudFrontList(serializers.Chain(
            serializers.Argument('cname'),
            serializers.Argument('aliases'),
        )),
        # We don't support GeoRestrictions yet - so include a stubbed default
        # when serializing
        'Restrictions': serializers.Const({
            'GeoRestriction': {
                'RestrictionType': 'none',
                'Quantity': 0,
            },
        }),
    }

    name = argument.String()
    cname = argument.String(default=lambda instance: instance.name, serializer=serializers.ListOfOne(maybe_empty=True))
    comment = argument.String(field='Comment', default=lambda instance: instance.name)
    aliases = argument.List()
    root_object = argument.String(default='/', field='DefaultRootObject')
    enabled = argument.Boolean(default=True, field='Enabled')
    origins = argument.ResourceList(
        (S3Origin, CustomOrigin, LoadBalancerOrigin),
        field='Origins',
        serializer=CloudFrontResourceList(),
    )
    default_cache_behavior = argument.Resource(
        DefaultCacheBehavior,
        field='DefaultCacheBehavior',
        serializer=serializers.Resource(),
    )
    behaviors = argument.ResourceList(
        CacheBehavior,
        field='CacheBehaviors',
        serializer=CloudFrontResourceList(),
    )
    error_responses = argument.ResourceList(
        ErrorResponse,
        field='CustomErrorResponses',
        serializer=CloudFrontResourceList(),
    )
    logging = argument.Resource(
        LoggingConfig,
        default=lambda instance: dict(enabled=False),
        field='Logging',
        serializer=serializers.Resource(),
    )
    price_class = argument.String(
        default='PriceClass_100',
        choices=['PriceClass_100', 'PriceClass_200', 'PriceClass_All'],
        field='PriceClass',
    )

    ssl_certificate = argument.Resource(
        ServerCertificate,
        field='Certificate',
        group='viewer-certificate',
        serializer=serializers.Property('ServerCertificateId'),
    )

    acm_certificate = argument.String(
        field='ACMCertificateArn',
        group='viewer-certificate',
    )

    ssl_support_method = argument.String(
        default='sni-only',
        choices=['sni-only', 'vip'],
        field='SSLSupportMethod',
        group='viewer-certificate',
    )

    ssl_minimum_protocol_version = argument.String(
        default='TLSv1',
        choices=['TLSv1', 'SSLv3', 'TLSv1.1_2016'],
        field='MinimumProtocolVersion',
        group='viewer-certificate',
    )

    viewer_certificate = argument.Serializer(
        field='ViewerCertificate',
        serializer=serializers.Resource(
            group='viewer-certificate',
            CertificateSource=serializers.Expression(
                lambda r, o: 'acm' if o.acm_certificate else 'iam' if o.ssl_certificate else 'cloudfront'
            ),
        ),
    )

    web_acl = argument.Resource(
        WebACL,
        field='WebACLId',
        empty_serializer=serializers.Const(''),
    )

    account = argument.Resource(BaseAccount)


class DistributionWaiter(Waiter):

    def get_waiter_filters(self):
        return {'Id': self.plan.object['Id']}


class Describe(SimpleDescribe, Plan):

    resource = Distribution
    service_name = 'cloudfront'
    api_version = '2016-01-28'
    describe_filters = {}
    describe_action = 'list_distributions'
    describe_envelope = 'DistributionList.Items'
    key = 'Id'

    def get_waiter(self, description, waiter, eventual_consistency_threshold=1):
        return DistributionWaiter(self, description, waiter, eventual_consistency_threshold)

    def describe_object_matches(self, d):
        return self.resource.name == d['Comment'] or self.resource.name in d['Aliases'].get('Items', [])

    def annotate_object(self, obj):
        result = self.client.get_distribution(Id=obj['Id'])
        distribution = {
            'ETag': result['ETag'],
            'Id': obj['Id'],
            'DomainName': result['Distribution']['DomainName'],
            'Status': result['Distribution']['Status'],
        }
        distribution.update(result['Distribution']['DistributionConfig'])
        return distribution


class Apply(SimpleApply, Describe):

    create_action = 'create_distribution'
    update_action = 'update_distribution'
    create_response = 'not-that-useful'
    waiter = 'distribution_deployed'

    signature = (
        Present('name'),
        Present('origins'),
        Present('default_cache_behavior'),
    )

    def get_create_serializer(self):
        return serializers.Dict(
            DistributionConfig=serializers.Resource(),
        )

    def get_update_serializer(self):
        return serializers.Dict(
            Id=serializers.Identifier(),
            DistributionConfig=serializers.Resource(),
            IfMatch=serializers.Property('ETag'),
        )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_distribution'

    def get_destroy_serializer(self):
        return serializers.Dict(
            Id=self.resource_id,
            IfMatch=serializers.Property('ETag'),
        )

    def destroy_object(self):
        if self.object.get('Enabled', False):
            yield self.generic_action(
                'Disable distribution',
                self.client.update_distribution,
                Id=self.object['Id'],
                IfMatch=self.object['ETag'],
                DistributionConfig=serializers.Resource(
                    Enabled=False,
                ),
            )

        if self.object.get('Enabled', False) or self.object.get('Status', '') == 'InProgress':
            yield self.get_waiter(
                ['Waiting for distribution to be disabled and enter state \'Deployed\''],
                'distribution_deployed',
            )

        if self.object.get('Enabled', False):
            yield RefreshMetadata(self)

        for change in super(Destroy, self).destroy_object():
            yield change


class AliasTarget(route53.AliasTarget):

    ''' Adapts a Distribution into a AliasTarget '''

    web_distribution = argument.Resource(
        Distribution,
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

    @classmethod
    def clean(cls, value):
        if isinstance(value, Distribution):
            return super(AliasTarget, cls).clean({'web_distribution': value})
        return super(AliasTarget, cls).clean(value)
