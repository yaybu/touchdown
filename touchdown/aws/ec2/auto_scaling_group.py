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
from touchdown.core import argument, errors, serializers

from touchdown import ssh

from ..account import BaseAccount
from ..elb import LoadBalancer
from ..vpc import Subnet
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy
from .launch_configuration import LaunchConfiguration


class AutoScalingGroup(Resource):

    resource_name = "auto_scaling_group"

    name = argument.String(field="AutoScalingGroupName")
    launch_configuration = argument.Resource(LaunchConfiguration, field="LaunchConfigurationName")
    min_size = argument.Integer(field="MinSize")
    max_size = argument.Integer(field="MaxSize")
    desired_capacity = argument.Integer(field="DesiredCapacity")
    default_cooldown = argument.Integer(default=300, field="DefaultCooldown")
    availability_zones = argument.List(field="AvailabilityZones", serializer=serializers.List(skip_empty=True))
    subnets = argument.ResourceList(
        Subnet,
        field="VPCZoneIdentifier",
        serializer=serializers.CommaSeperatedList(serializers.List(serializers.Identifier())),
    )
    load_balancers = argument.ResourceList(LoadBalancer, field="LoadBalancerNames", aws_update=False)
    health_check_type = argument.String(
        max=32,
        default=lambda instance: "ELB" if instance.load_balancers else None,
        field="HealthCheckType",
    )
    health_check_grace_period = argument.Integer(
        default=lambda instance: 480 if instance.load_balancers else None,
        field="HealthCheckGracePeriod",
    )
    placement_group = argument.String(max=255, field="PlacementGroup")
    termination_policies = argument.List(default=lambda i: ["Default"], field="TerminationPolicies")
    replacement_policy = argument.String(choices=['singleton', 'graceful'], default='graceful')

    account = argument.Resource(BaseAccount)


class ReplaceInstances(Action):

    scaling_processes = [
        "AlarmNotification",
        "AZRebalance",
        "ReplaceUnhealthy",
        "ScheduledActions",
    ]

    def __init__(self, plan, instance_ids):
        super(ReplaceInstances, self).__init__(plan)
        self.instance_ids = instance_ids
        self.desired_capacity = plan.object.get('DesiredCapacity', self.resource.min_size)

    @property
    def description(self):
        yield "Replace stale inances"
        for instance_id in self.instance_ids:
            yield instance_id

    def suspend_processes(self):
        self.plan.client.suspend_processes(
            AutoScalingGroupName=self.resource.name,
            ScalingProcesses=self.scaling_processes,
        )

    def terminate_instance(self, instance_id):
        self.plan.echo("Terminating instance {}".format(instance_id))
        self.plan.client.terminate_instance_in_auto_scaling_group(
            InstanceId=instance_id,
            ShouldDecrementDesiredCapacity=False,
        )

    def wait_for_healthy_asg(self):
        self.plan.echo("Waiting for scaling group to become healthy")
        while True:
            asg = self.plan.describe_object()
            if self.desired_capacity == len([i for i in asg['Instances'] if i['LifecycleState'] == 'InService']):
                return True
            time.sleep(5)

    def resume_processes(self):
        self.plan.client.resume_processes(
            AutoScalingGroupName=self.resource.name,
            ScalingProcesses=self.scaling_processes,
        )

    def run(self):
        self.plan.echo("Suspend autoscaling activities")
        self.suspend_processes()
        try:
            self.scale()
            try:
                for instance_id in self.instance_ids:
                    self.terminate_instance(instance_id)
                    self.wait_for_healthy_asg()
            finally:
                self.unscale()
        finally:
            self.plan.echo("Resuming autoscaling activities")
            self.resume_processes()

        # Make sure that our dependents have up to date intel on instances we
        # have just brought into service
        self.plan.object = self.plan.describe_object()


class GracefulReplacement(ReplaceInstances):

    def scale(self):
        self.plan.echo("Increasing scaling group capacity for node replacement")
        self.desired_capacity += 1

        max = self.resource.max_size
        if self.desired_capacity > max:
            max = self.desired_capacity

        self.plan.client.update_auto_scaling_group(
            AutoScalingGroupName=self.resource.name,
            MaxSize=max,
            DesiredCapacity=self.desired_capacity,
        )
        self.wait_for_healthy_asg()

    def unscale(self):
        self.plan.echo("Restoring scaling group to original capacity")
        self.desired_capacity -= 1
        self.plan.client.update_auto_scaling_group(
            AutoScalingGroupName=self.resource.name,
            MaxSize=self.resource.max_size,
            DesiredCapacity=min(self.resource.max_size, self.desired_capacity),
        )
        self.wait_for_healthy_asg()


class SingletonReplacement(ReplaceInstances):

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
        for change in super(Apply, self).update_object():
            yield change

        launch_config_name = self.runner.get_plan(self.resource.launch_configuration).resource_id
        instances = []

        for instance in self.object.get("Instances", []):
            if instance['LifecycleState'] in ('Terminating', ):
                continue
            if instance.get('LaunchConfigurationName', '') != launch_config_name:
                instances.append(instance['InstanceId'])

        if instances:
            klass = {
                'graceful': GracefulReplacement,
                'singleton': SingletonReplacement,
            }[self.resource.replacement_policy]

            yield klass(self, instances)


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


class Instance(ssh.Instance):

    resource_name = "random_asg_instance"
    input = AutoScalingGroup

    def get_serializer(self, runner):
        plan = runner.get_plan(self.adapts)

        plan.echo("Scanning for healthy instances to SSH to")

        # Annoyingly we have to get antother client (different API) to get info
        # on teh EC2 instances in our asg
        client = plan.session.create_client(
            service_name="ec2",
            region_name=plan.session.region,
            aws_access_key_id=plan.session.access_key_id,
            aws_secret_access_key=plan.session.secret_access_key,
            aws_session_token=plan.session.session_token,
        )

        reservations = client.describe_instances(
            InstanceIds=[
                i["InstanceId"] for i in plan.object.get("Instances", [])
            ],
        ).get("Reservations", [])

        instances = []
        for reservation in reservations:
            instances.extend(reservation.get("Instances", []))

        if len(instances) == 0:
            raise errors.Error("No instances available in {}".format(self.adapts))

        if hasattr(self.parent, "proxy") and self.parent.proxy and self.parent.proxy.instance and self.parent.proxy.instance.adapts.subnets[0].vpc == self.adapts.subnets[0].vpc:
            for instance in instances:
                if 'PrivateIpAddress' in instance:
                    return serializers.Const(instance['PrivateIpAddress'])

        for instance in instances:
            for k in ('PublicDnsName', 'PublicIpAddress'):
                if k in instance and instance[k]:
                    return serializers.Const(instance[k])

        raise errors.Error("No instances available in {} with ip address".format(self.adapts))
