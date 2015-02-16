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

from touchdown.core.resource import Resource
from touchdown.core.plan import Plan, Present
from touchdown.core import argument, serializers

from ..account import Account
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy

from ..iam import ServerCertificate
from ..s3 import Bucket

from .common import S3Origin, CloudFrontList, CloudFrontResourceList


class CustomOrigin(Resource):

    resource_name = "custom_origin"
    dot_ignore = True
    extra_serializers = {
        "CustomOriginConfig": serializers.Dict(
            HTTPPort=serializers.Argument("http_port"),
            HTTPSPort=serializers.Argument("https_port"),
            OriginProtocolPolicy=serializers.Argument("origin_protocol"),
        )
    }

    name = argument.String(field='Id')
    domain_name = argument.String(field='DomainName')
    http_port = argument.Integer(default=80)
    https_port = argument.Integer(default=443)
    origin_protocol = argument.String(choices=['http-only', 'match-viewer'], default='match-viewer')


class ForwardedValues(Resource):

    resource_name = "forwarded_values"
    dot_ignore = True

    extra_serializers = {
        "Cookies": serializers.Dict(
            Forward=serializers.Argument("forward_cookies"),
            WhitelistedNames=CloudFrontList(serializers.Argument("cookie_whitelist")),
        )
    }
    query_string = argument.Boolean(field="QueryString", default=False)
    headers = argument.List(field="Headers", serializer=CloudFrontList(serializers.List()))

    forward_cookies = argument.String(default="whitelist")
    cookie_whitelist = argument.List()


class DefaultCacheBehavior(Resource):

    resource_name = "default_cache_behaviour"
    dot_ignore = True

    extra_serializers = {
        # TrustedSigners are not supported yet, so include stub in serialized form
        "TrustedSigners": serializers.Const({
            "Enabled": False,
            "Quantity": 0,
        }),
        "AllowedMethods": CloudFrontList(
            inner=serializers.Context(serializers.Argument("allowed_methods"), serializers.List()),
            CachedMethods=serializers.Context(serializers.Argument("cached_methods"), CloudFrontList()),
        ),
    }

    target_origin = argument.String(field='TargetOriginId')
    forwarded_values = argument.Resource(
        ForwardedValues,
        default=lambda instance: dict(),
        field="ForwardedValues",
        serializer=serializers.Resource(),
    )
    viewer_protocol_policy = argument.String(choices=['allow-all', 'https-only', 'redirect-to-https'], default='allow-all', field="ViewerProtocolPolicy")
    min_ttl = argument.Integer(default=0, field="MinTTL")
    allowed_methods = argument.List(default=lambda x: ["GET", "HEAD"])
    cached_methods = argument.List(default=lambda x: ["GET", "HEAD"])
    smooth_streaming = argument.Boolean(default=False, field='SmoothStreaming')


class CacheBehavior(DefaultCacheBehavior):

    resource_name = "cache_behaviour"
    path_pattern = argument.String(field='PathPattern')


class ErrorResponse(Resource):

    resource_name = "error_response"
    dot_ignore = True

    error_code = argument.Integer(field="ErrorCode")
    response_page_path = argument.String(field="ResponsePagePath")
    response_code = argument.Integer(field="ResponseCode")
    min_ttl = argument.Integer(field="ErrorCachingMinTTL")


class LoggingConfig(Resource):

    resource_name = "logging_config"
    dot_ignore = True

    enabled = argument.Boolean(field="Enabled", default=False)
    include_cookies = argument.Boolean(field="IncludeCookies", default=False)
    bucket = argument.Resource(Bucket, field="Bucket", serializer=serializers.Default(default=None), default="")
    prefix = argument.String(field="Prefix", default="")


class ViewerCertificate(Resource):

    resource_name = "viewer_certificate"

    certificate = argument.Resource(
        ServerCertificate,
        field="IAMCertificateId",
        serializer=serializers.Property("ServerCertificateId"),
    )

    default_certificate = argument.Boolean(field="CloudFrontDefaultCertificate")

    ssl_support_method = argument.String(
        default="sni-only",
        choices=["sni-only", "vip"],
        field="SSLSupportMethod",
    )

    minimum_protocol_version = argument.String(
        default="TLSv1",
        choices=["TLSv1", "SSLv3"],
        field="MinimumProtocolVersion",
    )


class Distribution(Resource):

    resource_name = "distribution"

    extra_serializers = {
        "CallerReference": serializers.Expression(
            lambda runner, object: runner.get_plan(object).object.get('DistributionConfig', {}).get('CallerReference', str(uuid.uuid4()))
        ),
        "Aliases": CloudFrontList(serializers.Chain(
            serializers.Context(serializers.Argument("name"), serializers.ListOfOne()),
            serializers.Context(serializers.Argument("aliases"), serializers.List()),
        )),
        # We don't support GeoRestrictions yet - so include a stubbed default
        # when serializing
        "Restrictions": serializers.Const({
            "GeoRestriction": {
                "RestrictionType": "none",
                "Quantity": 0,
            },
        }),
    }

    name = argument.String()
    comment = argument.String(field='Comment', default=lambda instance: instance.name)
    aliases = argument.List()
    root_object = argument.String(default='/', field="DefaultRootObject")
    enabled = argument.Boolean(default=True, field="Enabled")
    origins = argument.ResourceList(
        (S3Origin, CustomOrigin),
        field="Origins",
        serializer=CloudFrontResourceList(),
    )
    default_cache_behavior = argument.Resource(
        DefaultCacheBehavior,
        field="DefaultCacheBehavior",
        serializer=serializers.Resource(),
    )
    behaviors = argument.ResourceList(
        CacheBehavior,
        field="CacheBehaviors",
        serializer=CloudFrontResourceList(),
    )
    error_responses = argument.ResourceList(
        ErrorResponse,
        field="CustomErrorResponses",
        serializer=CloudFrontResourceList(),
    )
    logging = argument.Resource(
        LoggingConfig,
        default=lambda instance: dict(enabled=False),
        field="Logging",
        serializer=serializers.Resource(),
    )
    price_class = argument.String(
        default="PriceClass_100",
        choices=['PriceClass_100', 'PriceClass_200', 'PriceClass_All'],
        field="PriceClass",
    )
    viewer_certificate = argument.Resource(
        ViewerCertificate,
        field="ViewerCertificate",
        serializer=serializers.Resource(),
    )

    account = argument.Resource(Account)


class Describe(SimpleDescribe, Plan):

    resource = Distribution
    service_name = 'cloudfront'
    describe_filters = {}
    describe_action = "list_distributions"
    describe_envelope = 'DistributionList.Items'
    key = 'Id'

    def get_describe_filters(self):
        return {"Id": self.object['Id']}

    def describe_object_matches(self, d):
        return self.resource.name in d['Aliases'].get('Items', [])

    def describe_object(self):
        distribution = super(Describe, self).describe_object()
        if distribution:
            result = self.client.get_distribution(Id=distribution['Id'])
            distribution = {"ETag": result["ETag"], "Id": distribution["Id"]}
            distribution.update(result['Distribution'])
            return distribution


class Apply(SimpleApply, Describe):

    create_action = "create_distribution"
    create_response = "not-that-useful"
    waiter = "distribution_deployed"

    signature = (
        Present("name"),
        Present("origins"),
        Present("default_cache_behavior"),
    )

    def get_create_serializer(self):
        return serializers.Dict(
            DistributionConfig=serializers.Resource(),
        )


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_distribution"

    def get_destroy_serializer(self):
        return serializers.Dict(
            Id=self.resource_id,
            IfMatch=self.object['ETag'],
        )

    def destroy_object(self):
        if not self.object:
            return

        if self.object['DistributionConfig'].get('Enabled', False):
            yield self.generic_action(
                "Disable distribution",
                self.client.update_distribution,
                Id=self.object['Id'],
                IfMatch=self.object['ETag'],
                DistributionConfig=serializers.Resource(
                    Enabled=False,
                ),
            )

            yield self.get_waiter(
                ["Waiting for distribution to enter disabled state"],
                "distribution_deployed",
            )

        for change in super(Destroy, self).destroy_object():
            yield change
