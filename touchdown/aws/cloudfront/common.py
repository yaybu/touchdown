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

from touchdown.core import argument, serializers
from touchdown.core.resource import Resource

from ..s3 import Bucket


class CloudFrontList(serializers.Dict):

    def __init__(self, inner=None, **kwargs):
        self.kwargs = dict(kwargs)
        self.kwargs['Items'] = inner or serializers.List()
        self.kwargs['Quantity'] = serializers.Expression(
            lambda runner, object: len(self.kwargs['Items'].render(runner, object)),
        )

    def diff(self, runner, obj, value):
        if len(self.kwargs) == 2:
            items = value['Items'] if value else []
            return self.kwargs['Items'].diff(runner, obj, items)
        return super(CloudFrontList, self).diff(runner, obj, value)


def CloudFrontResourceList():
    return CloudFrontList(serializers.List(serializers.Resource()))


class S3Origin(Resource):

    resource_name = 's3_origin'
    extra_serializers = {
        'S3OriginConfig': serializers.Dict(
            OriginAccessIdentity=serializers.Argument('origin_access_identity'),
        ),
        'CustomHeaders': serializers.Dict(
            Quantity=0,
            Items=[],
        ),
    }

    name = argument.String(field='Id')
    bucket = argument.Resource(Bucket, field='DomainName', serializer=serializers.Format('{0}.s3.amazonaws.com', serializers.Identifier()))
    origin_path = argument.String(default='', field='OriginPath')
    origin_access_identity = argument.String(default='')
