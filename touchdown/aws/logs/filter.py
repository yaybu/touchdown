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
from touchdown.core.plan import Plan, Present

from ..common import Resource, SimpleApply, SimpleDescribe, SimpleDestroy
from .group import LogGroup


class Transformation(Resource):

    resource_name = 'transformation'

    name = argument.String(field='metricName')
    namespace = argument.String(field='metricNamespace')
    value = argument.String(field='metricValue')


class Filter(Resource):

    resource_name = 'filter'

    name = argument.String(min=1, max=512, field='filterName')
    log_group = argument.Resource(LogGroup, field='logGroupName', update=False)
    pattern = argument.String(min=1, max=512, field='filterPattern')

    transformations = argument.ResourceList(
        Transformation,
        min=1,
        field='metricTransformations',
        serializer=serializers.List(serializers.Resource()),
    )


class Describe(SimpleDescribe, Plan):

    resource = Filter
    service_name = 'logs'
    api_version = '2014-03-28'
    describe_action = 'describe_metric_filters'
    describe_notfound_exception = 'ResourceNotFoundException'
    describe_envelope = 'metricFilters'
    key = 'filterName'

    def get_describe_filters(self):
        return {
            'logGroupName': self.resource.log_group.name,
            'filterNamePrefix': self.resource.name
        }


class Apply(SimpleApply, Describe):

    signature = (Present('name'), Present('pattern'), Present('transformations'))

    create_action = 'put_metric_filter'
    update_action = 'put_metric_filter'
    create_response = 'nothing-useful'


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_metric_filter'

    def get_destroy_serializer(self):
        return serializers.Dict(
            logGroupName=self.resource.log_group.name,
            filterName=self.resource.name,
        )
