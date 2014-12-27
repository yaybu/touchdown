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
from touchdown.core.action import Action
from touchdown.core import argument, errors

from ..common import SimpleApply


class AutoScalingGroup(Resource):

    resource_name = "auto_scaling_group"

    """ A name for this AutoScalingGroup. Unique within an AWS account """
    name = argument.String()

    """ The minimum number of EC2 instances that must be running """
    min_size = argument.Integer()

    """ The maximum number of EC2 instances that can be started by this
    AutoScalingGroup """
    max_size = argument.Integer()

    """ The number of EC2 instances that should be running. Must be between
    min_size and max_size. """
    desired_capacity = argument.Integer()

    """ The amount of time (in seconds) between scaling activities. """
    default_cooldown = argument.Integer(default=300)


class AddAutoScalingGroup(Action):

    @property
    def description(self):
        yield "Create AutoScalingGroup"

    def run(self):
        self.target.object = self.target.client.create_auto_scaling_group(
            AutoScalingGroupName=self.resource.name,
            MinSize=self.resource.min_size,
            MaxSize=self.resource.max_size,
            DesiredCapacity=self.resource.desired_capacity,
            DefaultCooldown=self.resource.default_cooldown,
        )


class Apply(SimpleApply, Target):

    resource = AutoScalingGroup
    add_action = AddAutoScalingGroup
    key = 'AutoScalingGroupId'

    def get_object(self, runner):
        asgs = self.client.describe_auto_scaling_groups(
            AutoScalingGroupNames=[self.resource.name],
        )
        if data['Asg']:
            return data['Asg'][0]
