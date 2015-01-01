# Copyright 2014 Isotoma Limited
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
from ..elb import LoadBalancer
from ..common import SimpleApply
from .launch_configuration import LaunchConfiguration


class AutoScalingGroup(Resource):

    resource_name = "auto_scaling_group"

    """ A name for this AutoScalingGroup. Unique within an AWS account """
    name = argument.String(aws_field="AutoScalingGroupName")

    """ A launch configuration """
    launch_configuration = argument.Resource(LaunchConfiguration, aws_field="LaunchConfigurationName")

    """ The minimum number of EC2 instances that must be running """
    min_size = argument.Integer(aws_field="MinSize")

    """ The maximum number of EC2 instances that can be started by this
    AutoScalingGroup """
    max_size = argument.Integer(aws_field="MaxSize")

    """ The number of EC2 instances that should be running. Must be between
    min_size and max_size. """
    desired_capacity = argument.Integer(aws_field="DesiredCapacity")

    """ The amount of time (in seconds) between scaling activities. """
    default_cooldown = argument.Integer(default=300, aws_field="DefaultCooldown")

    availability_zones = argument.List(aws_field="AvailabilityZones")

    load_balancers = argument.ResourceList(LoadBalancer, aws_field="LoadBalancerNames", aws_update=False)

    health_check_type = argument.String(max=32, aws_field="HealthCheckType")

    health_check_grace_period = argument.String(aws_field="HealthCheckGracePeriod")

    placement_group = argument.String(max=255, aws_field="PlacementGroup")

    termination_policies = argument.List(aws_field="TerminationPolicies")

    account = argument.Resource(AWS)


class Apply(SimpleApply, Target):

    resource = AutoScalingGroup
    create_action = "create_auto_scaling_group"
    update_action = "update_auto_scaling_group"
    describe_action = "describe_auto_scaling_groups"
    describe_list_key = "AutoScalingGroups"
    key = 'AutoScalingGroupName'

    @property
    def client(self):
        account = self.runner.get_target(self.resource.acount)
        return account.get_client('autoscale')
