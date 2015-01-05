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
from touchdown.core.target import Target
from touchdown.core import argument

from ..account import AWS
from ..common import SimpleApply
from .. import serializers

from ..iam import ServerCertificate
from ..s3 import Bucket


class CloudFrontList(serializers.Formatter):

    def render(self, runner, object):
        result = self.inner.render(runner, object)
        return {
            "Quantity": len(result),
            "Items": result,
        }


def CloudFrontResourceList():
    return CloudFrontList(serializers.List(serializers.Resource()))


class Origin(Resource):

    resource_name = "origin"

    extra_serializers = {
        "S3OriginConfig": serializers.Dict(
            OriginAccessIdentity=serializers.Argument("origin_access_identity"),
        ),
        "CustomOriginConfig": serializers.Dict(
            HttpPort=serializers.Argument("http_port"),
            HttpsPort=serializers.Argument("https_port"),
            OriginProtocol=serializers.Argument("origin_protocol"),
        )
    }

    name = argument.String(aws_field='Id')
    origin_type = argument.String(choices=['s3', 'custom'])
    domain_name = argument.String(aws_field='DomainName')

    # Only valid for S3 origins...
    origin_access_identity = argument.String()

    # Only valid for Custom origins
    http_port = argument.Integer(default=80)
    https_port = argument.Integer(default=443)
    origin_protocol = argument.String(choices=['http-only', 'match-viewer'], default='match-viewer')


class ForwardedValues(Resource):

    resource_name = "forwarded_values"

    extra_serializers = {
        "CookiePreference": dict(
            Forward=serializers.Argument("forward_cookies"),
            WhitelistedNames=CloudFrontList(serializers.Argument("cookie_whitelist")),
        )
    }
    query_string = argument.Boolean(aws_field="QueryString")
    headers = argument.List(aws_field="Headers", aws_serializer=CloudFrontList(serializers.List()))

    forward_cookies = argument.String()
    cookie_whitelist = argument.List()


class DefaultCacheBehavior(Resource):

    resource_name = "default_cache_behaviour"

    extra_serializers = {
        # TrustedSigners are not supported yet, so include stub in serialized form
        "TrustedSigners": serializers.Const({
            "Enabled": False,
            "Quantity": 0,
        })
    }

    target_origin = argument.String(aws_field='TargetOriginId')
    forwarded_values = argument.Resource(ForwardedValues, aws_field="ForwardedValues")
    viewer_protocol_policy = argument.String(choices=['allow-all', 'https-only', 'redirect-to-https'], default='allow-all')
    min_ttl = argument.Integer(default=0, aws_field="MinTTL")
    allowed_methods = argument.List(
        default=lambda x: ["GET", "HEAD"],
        aws_field='AllowedMethods',
        aws_serializer=CloudFrontList(),
    )
    smooth_streaming = argument.Boolean(default=False, aws_field='SmoothStreaming')


class CacheBehavior(DefaultCacheBehavior):

    resource_name = "cache_behaviour"
    path_pattern = argument.String(aws_field='PathPattern')


class ErrorResponse(Resource):

    resource_name = "error_response"

    error_code = argument.Integer(aws_field="ErrorCode")
    response_page_path = argument.String(aws_field="ResponsePagePath")
    response_code = argument.Integer(aws_field="ResponseCode")
    min_ttl = argument.Integer(aws_field="ErrorCachingMinTTL")


class LoggingConfig(Resource):

    resource_name = "logging_config"

    enabled = argument.Boolean(aws_field="Enabled")
    include_cookies = argument.Boolean(aws_field="IncludeCookies")
    bucket = argument.Resource(Bucket, aws_field="Bucket")
    prefix = argument.String(aws_field="Prefix")


class ViewerCertificate(Resource):

    resource_name = "viewer_certificate"

    certificate = argument.Resource(
        ServerCertificate,
        aws_field="IAMCertificateId",
        aws_serializers=serializers.Property("IAMCertificateId"),
    )

    default_certificate = argument.Boolean(aws_field="CloudFrontDefaultCertificate")

    ssl_support_method = argument.String(
        default="sni-only",
        choices=["sni-only", "vip"],
        aws_field="SSLSupportMethod",
    )

    minimum_protocol_version = argument.String(
        default="TLSv1",
        choices=["TLSv1", "SSLv3"],
        aws_field="MinimumProtocolVersion",
    )


class Distribution(Resource):

    resource_name = "distributions"

    extra_serializers = {
        "Aliases": CloudFrontList(serializers.Chain(
            serializers.Context(serializers.Argument("name"), serializers.ListOfOne()),
            serializers.Context(serializers.Argument("aliases"), serializers.List()),
        )),
        # We don't support GeoRestrictions yet - so include a stubbed default
        # when serializing
        "Restrictions": serializers.Const({
            "GeoRestriction": {
                "RestrictionType": "none",
            },
        }),
    }

    """ The name of the distribution. This should be the primary domain that it
    responds to. """
    name = argument.String()

    """ Any comments you want to include about the distribution. """
    comment = argument.String(aws_field='Comment')

    """ Alternative names that the distribution should respond to. """
    aliases = argument.List()

    """ The default URL to serve when the users hits the root URL. For example
    if you want to serve index.html when the user hits www.yoursite.com then
    set this to '/index.html' """
    root_object = argument.String(default='/', aws_field="DefaultRootObject")

    """ Whether or not this distribution is active """
    enabled = argument.Boolean(default=True, aws_field="Enabled")

    origins = argument.ResourceList(
        Origin,
        aws_field="Origins",
        aws_serializer=CloudFrontResourceList(),
    )

    default_cache_behavior = argument.Resource(
        DefaultCacheBehavior,
        aws_field="DefaultCacheBehavior",
        aws_serializer=CloudFrontResourceList(),
    )

    behaviors = argument.ResourceList(
        CacheBehavior,
        aws_field="CacheBehaviors",
        aws_serializer=CloudFrontResourceList(),
    )

    """ Customize the content that is served for various error conditions """
    error_responses = argument.ResourceList(
        ErrorResponse,
        aws_field="CustomErrorResponses",
        aws_serializer=CloudFrontResourceList(),
    )

    logging = argument.Resource(
        LoggingConfig,
        aws_field="Logging",
        aws_serializer=serializers.Resource(),
    )

    price_class = argument.String(
        default="PriceClass_100",
        choices=['PriceClass_100', 'PriceClass_200', 'PriceClass_All'],
        aws_field="PriceClass",
    )

    certificate = argument.Resource(
        ViewerCertificate,
        aws_field="ViewerCertificate",
        aws_serializers=serializers.Resource(),
    )

    account = argument.Resource(AWS)


class Apply(SimpleApply, Target):

    resource = Distribution
    service_name = 'cloudfront'
    create_action = "create_distribution"
    get_action = "get_distribution"
    key = 'Id'
