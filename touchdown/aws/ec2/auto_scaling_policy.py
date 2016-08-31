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
from touchdown.core.plan import Plan, Present
from touchdown.core.resource import Resource

from .. import cloudwatch
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy
from .auto_scaling_group import AutoScalingGroup


class Policy(Resource):

    resource_name = 'policy'

    name = argument.String(field='PolicyName')
    auto_scaling_group = argument.Resource(AutoScalingGroup, field='AutoScalingGroupName')

    min_adjustment_step = argument.Integer(field='MinAdjustmentStep')
    adjustment_type = argument.String(
        choices=['ChangeInCapacity', 'ExactCapacity', 'PercentChangeInCapacity'],
        default='ChangeInCapacity',
        field='AdjustmentType'
    )
    scaling_adjustment = argument.Integer(default=1, field='ScalingAdjustment')
    cooldown = argument.Integer(default=30, field='Cooldown')

    # alarms = argument.ResourceList('touchdown.aws.cloudwatch.Alarm', field='Alarms')


class Describe(SimpleDescribe, Plan):

    resource = Policy
    service_name = 'autoscaling'
    api_version = '2011-01-01'
    describe_action = 'describe_policies'
    describe_envelope = 'ScalingPolicies'
    key = 'PolicyName'

    def get_describe_filters(self):
        asg = self.runner.get_plan(self.resource.auto_scaling_group)
        if not asg.resource_id:
            return None

        return {
            'AutoScalingGroupName': self.resource.auto_scaling_group.name,
            'PolicyNames': [self.resource.name]
        }


class Apply(SimpleApply, Describe):

    create_action = 'put_scaling_policy'
    create_response = 'not-that-useful'

    signature = (
        Present('name'),
        Present('auto_scaling_group'),
    )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_policy'

    def get_destroy_serializer(self):
        return serializers.Dict(
            AutoScalingGroupName=self.resource.auto_scaling_group.name,
            PolicyName=self.resource.name,
        )


class AlarmDestination(cloudwatch.AlarmDestination):

    resource_name = 'alarm_destination'
    input = Policy

    def get_serializer(self, runner, **kwargs):
        return self.adapts.get_property('PolicyARN')
