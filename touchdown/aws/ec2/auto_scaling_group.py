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

import time

from touchdown.core.action import Action
from touchdown.core.resource import Resource
from touchdown.core.plan import Plan
from touchdown.core import argument, errors

from ..account import Account
from touchdown.core import serializers
from ..elb import LoadBalancer
from ..vpc import Subnet
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy
from .launch_configuration import LaunchConfiguration


class AutoScalingGroup(Resource):

    resource_name = "auto_scaling_group"

    name = argument.String(field="AutoScalingGroupName")
    """ A name for this AutoScalingGroup. Unique within an AWS account """

    launch_configuration = argument.Resource(LaunchConfiguration, field="LaunchConfigurationName")
    """ A :py:class:`LaunchConfiguration`. """

    min_size = argument.Integer(field="MinSize")
    """ The minimum number of EC2 instances that must be running """

    max_size = argument.Integer(field="MaxSize")
    """ The maximum number of EC2 instances that can be started by this
    AutoScalingGroup """

    desired_capacity = argument.Integer(field="DesiredCapacity")
    """ The number of EC2 instances that should be running. Must be between
    min_size and max_size. """

    default_cooldown = argument.Integer(default=300, field="DefaultCooldown")
    """ The amount of time (in seconds) between scaling activities. """

    availability_zones = argument.List(field="AvailabilityZones", serializer=serializers.List(skip_empty=True))

    subnets = argument.ResourceList(
        Subnet,
        field="VPCZoneIdentifier",
        serializer=serializers.CommaSeperatedList(serializers.List(serializers.Identifier())),
    )
    """ A list of :py:class:`touchdown.aws.vpc.Subnet` resources """

    load_balancers = argument.ResourceList(LoadBalancer, field="LoadBalancerNames", aws_update=False)
    """ A list of :py:class:`touchdown.aws.elb.LoadBalancer` resources. As
    instances are created by the auto scaling group they are added to these
    load balancers. """

    health_check_type = argument.String(
        max=32,
        default=lambda instance: "ELB" if instance.load_balancers else None,
        field="HealthCheckType",
    )
    """ The kind of health check to use to detect unhealthy instances. By
    default if you are using ELB with the ASG it will use the same health
    checks as ELB. """

    health_check_grace_period = argument.Integer(
        default=lambda instance: 60 if instance.load_balancers else None,
        field="HealthCheckGracePeriod",
    )

    placement_group = argument.String(max=255, field="PlacementGroup")

    termination_policies = argument.List(field="TerminationPolicies")

    replacement_policy = argument.String(choices=['singleton', 'graceful'], default='graceful')

    account = argument.Resource(Account)


class ReplaceInstance(Action):

    scaling_processes = [
        "AlarmNotification",
        "AZRebalance",
        "ReplaceUnhealthy",
        "ScheduledActions",
    ]

    def __init__(self, plan, instance_id):
        super(ReplaceInstance, self).__init__(plan)
        self.instance_id = instance_id

    def suspend_processes(self):
        self.client.suspend_processes(
            AutoScalingGroupName=self.resource.name,
            ScalingProcesses=self.scaling_processes,
        )

    def scale(self):
        raise NotImplementedError(self.scale)

    # FIXME: If TerminateInstanceInAutoScalingGroup is graceful then we don't
    # need to detach from the ASG.
    """
    def remove_from_balancer(self):
        self.client.detach_instances(
            AutoScalingGroupName=self.resource.name,
            InstanceIds=[self.instance_id],
            ShouldDecrementDesiredCapacity=False,
        )
    """

    def terminate_instance(self):
        self.client.terminate_instance_in_auto_scaling_group(
            InstanceId=self.instance_id,
            ShouldDecrementDesiredCapacity=False,
        )

    def wait_for_healthy_asg(self):
        # FIXME: Consider the grace period of the ASG + few minutes for booting
        # and use that as a timeout for the release process.
        while True:
            asg = self.plan.describe_object()
            if asg['DesiredCapacity'] == len(i for i in asg['Instances'] if i['HealthStatus'] == 'Healthy'):
                return True

    def unscale(self):
        raise NotImplementedError(self.unscale)

    def resume_processes(self):
        self.client.resume_processes(
            AutoScalingGroupName=self.resource.name,
            ScalingProcesses=self.scaling_processes,
        )

    def run(self):
        self.suspend_processes()
        try:
            self.scale()
            try:
                # self.remove_from_balancer()
                self.terminate_instance()
                if not self.wait_for_healthy_asg():
                    raise errors.Error("Auto scaling group {} is not returning to a healthy state".format(self.resource.name))
            finally:
                self.unscale()
        finally:
            self.resume_processes()


class GracefulReplacement(ReplaceInstance):

    @property
    def description(self):
        yield "Gracefully replace instance {} (by increasing ASG pool and then terminating)".format(self.instance_id)

    def scale(self):
        desired_capacity = self.plan.object['DesiredCapacity']
        desired_capacity += 1

        max = self.resource.max
        if desired_capacity > max:
            max = desired_capacity

        self.client.update_auto_scaling_group(
            AutoScalingGroupName=self.resource.name,
            MaxSize=max,
            DesiredCapacity=desired_capacity,
        )

    def unscale(self):
        self.client.update_auto_scaling_group(
            AutoScalingGroupName=self.resource.name,
            MaxSize=self.resource.max,
            DesiredCapacity=self.object['DesiredCapacity'],
        )


class SingletonReplacement(Action):

    @property
    def description(self):
        yield "Replace singleton instance {}".format(self.instance_id)

    def scale(self):
        pass

    def unscale(self):
        pass


class Describe(SimpleDescribe, Plan):

    resource = AutoScalingGroup
    service_name = 'autoscaling'
    describe_action = "describe_auto_scaling_groups"
    describe_list_key = "AutoScalingGroups"
    key = 'AutoScalingGroupName'

    def get_describe_filters(self):
        return {"AutoScalingGroupNames": [self.resource.name]}


class Apply(SimpleApply, Describe):

    create_action = "create_auto_scaling_group"
    create_response = "not-that-useful"
    update_action = "update_auto_scaling_group"

    def update_object(self):
        launch_config_name = self.runner.get_plan(self.resource.launch_configuration).resource_id

        for instance in self.object.get("Instances", []):
            if instance['LifecycleState'] in ('Terminating', ):
                continue
            if instance.get('LaunchConfigurationName', '') != launch_config_name:
                klass = {
                    'graceful': GracefulReplacement,
                    'singleton': SingletonReplacement,
                }[self.resource.replacement_policy]

                yield klass(self, instance['InstanceId'])


class TerminateASGInstances(Action):

    @property
    def description(self):
        yield "Scale down and wait for {} instances to terminate".format(
            len(self.plan.object.get('Instances', []))
        )
        for instance in self.plan.object.get('Instances', []):
            yield instance['InstanceId']

    def run(self):
        # Destroy all the instances in the ASG
        self.plan.client.update_auto_scaling_group(
            AutoScalingGroupName=self.resource.name,
            MinSize=0,
            MaxSize=0,
            DesiredCapacity=0,
        )

        # Wait until all the ASG instances have gone away
        while True:
            asg = self.plan.describe_object()
            if len(asg.get("Instances", [])) == 0:
                break
            time.sleep(10)

        # Wait until any ASG activies have stopped
        while True:
            activities = self.plan.client.describe_scaling_activities(AutoScalingGroupName=self.resource.name)['Activities']
            if len(tuple(a for a in activities if a['StatusCode'] == 'InProgress')) == 0:
                break
            time.sleep(10)


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_auto_scaling_group"

    def destroy_object(self):
        yield TerminateASGInstances(self)
        for change in super(Destroy, self).destroy_object():
            yield change
