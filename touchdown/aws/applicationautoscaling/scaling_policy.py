# Copyright 2016 John Carr
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
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy

from .scalable_target import ScalableTarget


class StepAdjustment(Resource):

    resource_name = 'step_adjustment'

    metric_interval_lower_bound = argument.Float(field='MetricIntervalLowerBound')
    metric_interval_upper_bound = argument.Float(field='MetricIntervalUpperBound')
    scaling_adjustment = argument.Integer(field='ScalingAdjustment')


class ScalingPolicy(Resource):

    resource_name = 'scaling_policy'

    name = argument.String(field='PolicyName')

    scalable_target = argument.Resource(
        ScalableTarget,
        field='ResourceId',
        serializer=serializers.Expression(lambda x, y: '...'),
    )
    _service_namespace = argument.Callable(
        lambda instance: instance.scalable_target.service if instance.scalable_target else None,
        field='ServiceNamespace',
    )
    _scalable_dimension = argument.Callable(
        lambda instance: instance.scalable_target.scalable_dimension if instance.scalable_target else None,
        field='ScalableDimension',
    )

    policy_type = argument.String(
        field='PolicyType',
        default='StepScaling',
        choices=['StepScaling'],
    )

    adjustment_type = argument.String(
        field='AdjustmentType',
        group='StepScalingPolicyConfiguration',
        choices=[
            'ChangeInCapacity',
            'PercentChangeInCapacity',
            'ExactCapacity',
        ],
    )

    step_adjustments = argument.List(
        argument.Resource(StepAdjustment),
        field='StepAdjustments',
        group='StepScalingPolicyConfiguration',
    )

    min_adjustment_magnitude = argument.Integer(
        field='MinAdjustmentMagnitude',
        group='StepScalingPolicyConfiguration',
    )

    cooldown = argument.Integer(
        field='Cooldown',
        group='StepScalingPolicyConfiguration',
    )

    metric_aggregation_type = argument.String(
        field='MetricAggregationType',
        group='StepScalingPolicyConfiguration',
        choices=[
            'Average',
            'Minimum',
            'Maximum',
        ]
    )

    _StepScalingPolicyConfiguration = argument.Serializer(
        serializers.Resource(
            field='StepScalingPolicyConfiguration',
            group='StepScalingPolicyConfiguration',
        )
    )

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = ScalingPolicy
    service_name = 'application-autoscaling'
    describe_action = 'describe_scaling_policies'
    describe_envelope = 'ScalingPolicies'
    key = 'PolicyName'

    def get_describe_filters(self):
        return {
            'PolicyNames': [self.resource.name],
            'ServiceNamespace': self.resource.scalable_target.service,
        }


class Apply(SimpleApply, Describe):

    create_action = 'put_scaling_policy'
    create_response = 'not-that-useful'


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_scaling_policy'

    def get_destroy_serializer(self):
        return serializers.Dict(
            PolicyName=self.resource.name,
            ServiceNamespace=self.resource.scalable_target.service,
            ResourceId=self.resource.scalable_target.resource,
            ScalableDimension=self.resource.scalable_target.scalable_dimension,
        )
