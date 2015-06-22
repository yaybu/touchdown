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

from touchdown.core.resource import Resource
from touchdown.core.plan import Plan, Present
from touchdown.core import argument, serializers
from touchdown.core.adapters import Adapter

from ..common import SimpleDescribe, SimpleApply, SimpleDestroy
from .metric import Metric


class AlarmDestination(Adapter):
    pass


class Dimension(Resource):

    name = argument.String(field="Name", min=1, max=255)
    value = argument.String(field="Value", min=1, max=255)


class Alarm(Resource):

    resource_name = "alarm"

    name = argument.String(field="AlarmName")
    description = argument.String(field="AlarmDescription")
    actions_enabled = argument.Boolean(field="ActionsEnabled")
    ok_actions = argument.ResourceList(AlarmDestination, field="OKActions")
    alarm_actions = argument.ResourceList(AlarmDestination, field="AlarmActions")
    insufficient_data_actions = argument.ResourceList(AlarmDestination, field="InsufficientDataActions")

    statistic = argument.String(choice=["SampleCount", "Average", "Sum", "Minimum", "Maximum"], field="Statistic")
    dimensions = argument.ResourceList(Dimension, max=10, field="Dimensions")
    period = argument.Integer(min=60, field="Period")
    unit = argument.String(field="Unit", choices=[
        "Seconds",
        "Microseconds",
        "Milliseconds",
        "Bytes",
        "Kilobytes",
        "Megabytes",
        "Gigabytes",
        "Terabytes",
        "Bits",
        "Kilobits",
        "Megabits",
        "Gigabits",
        "Terabits",
        "Percent",
        "Count",
        "Bytes/Second",
        "Kilobytes/Second",
        "Megabytes/Second",
        "Gigabytes/Second",
        "Terabytes/Second",
        "Bits/Second",
        "Kilobits/Second",
        "Megabits/Second",
        "Gigabits/Second",
        "Terabits/Second",
        "Count/Second",
        "None",
    ])
    evaluation_periods = argument.Integer(min=1, field="EvaluationPeriods")
    threshold = argument.Integer(field="Threshold")
    comparison_operator = argument.String(choices=[
        "GreaterThanOrEqualToThreshold",
        "GreaterThanThreshold",
        "LessThanThreshold",
        "LessThanOrEqualToThreshold",
    ])

    metric = argument.Resource(Metric, field="MetricName")


class Describe(SimpleDescribe, Plan):

    resource = Alarm
    service_name = 'cloudwatch'
    describe_action = "describe_alarms_for_metric"
    describe_envelope = "MetricAlarms"
    describe_filters = {}
    key = 'MetricAlarm'

    def describe_object_matches(self, role):
        return role['AlarmName'] == self.resource.name


class Apply(SimpleApply, Describe):

    create_action = "put_metric_alarm"

    signature = [
        Present("name"),
        Present("metric"),
        Present("namespace"),
        Present("statistic"),
        Present("period"),
        Present("evaluation_periods"),
        Present("threshold"),
        Present("comparison_operator"),
    ]


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_alarms"

    def get_destroy_serializer(self):
        return serializers.Dict(
            AlarmNames=[self.resource.name],
        )
