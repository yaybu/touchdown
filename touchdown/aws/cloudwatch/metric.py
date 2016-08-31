# Copyright 2015 Isotoma Limited
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
from touchdown.core.plan import Plan
from touchdown.core.resource import Resource

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe


class Metric(Resource):

    resource_name = 'metric'

    name = argument.String(field='MetricName')
    namespace = argument.String(field='Namespace')

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = Metric
    service_name = 'cloudwatch'
    api_version = '2010-08-01'
    describe_action = 'list_metrics'
    describe_envelope = 'Metrics'
    key = 'MetricName'

    def get_describe_filters(self):
        return {
            self.key: self.resource.name,
            'Namespace': self.resource.namespace,
        }


class Apply(SimpleApply, Describe):

    create_action = 'put_metric_data'

    def get_create_serializer(self):
        return serializers.Dict(
            Namespace=serializers.Argument('namespace'),
            MetricData=serializers.ListOfOne(
                serializers.Dict(
                    MetricName=serializers.Argument('name'),
                    Value=0,
                )
            )
        )
