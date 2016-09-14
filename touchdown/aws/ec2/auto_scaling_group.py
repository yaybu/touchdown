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

import random
import time

from touchdown import ssh
from touchdown.core import argument, errors, serializers
from touchdown.core.action import Action
from touchdown.core.plan import Plan, Present
from touchdown.core.resource import Resource
from touchdown.core.utils import cached_property

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy
from ..elb import LoadBalancer
from ..vpc import Subnet
from .launch_configuration import LaunchConfiguration


class AutoScalingGroupTag(Resource):

    resource_name = 'auto_scaling_group_tag'

    resource_type = argument.Serializer(serializer=serializers.Const('auto-scaling-group'), field='ResourceType')
    resource_id = argument.Callable(lambda x: x.parent.name, field='ResourceId')

    name = argument.String(field='Key', min=1, max=127)
    value = argument.String(field='Value', min=0, max=255)
    propagate = argument.Boolean(field='PropagateAtLaunch', default=True)


class AutoScalingGroup(Resource):

    resource_name = 'auto_scaling_group'

    name = argument.String(field='AutoScalingGroupName')
    launch_configuration = argument.Resource(LaunchConfiguration, field='LaunchConfigurationName')
    min_size = argument.Integer(min=0, field='MinSize')
    max_size = argument.Integer(min=0, field='MaxSize')
    desired_capacity = argument.Integer(field='DesiredCapacity')
    default_cooldown = argument.Integer(default=300, field='DefaultCooldown')

    subnets = argument.ResourceList(
        Subnet,
        field='VPCZoneIdentifier',
        serializer=serializers.CommaSeperatedList(serializers.List(serializers.Identifier(), skip_empty=True)),
    )

    load_balancers = argument.ResourceList(LoadBalancer, field='LoadBalancerNames', update=False)
    health_check_type = argument.String(
        max=32,
        default=lambda instance: 'ELB' if instance.load_balancers else None,
        field='HealthCheckType',
    )
    health_check_grace_period = argument.Integer(
        default=lambda instance: 480 if instance.load_balancers else None,
        field='HealthCheckGracePeriod',
    )
    placement_group = argument.String(max=255, field='PlacementGroup')
    termination_policies = argument.List(default=lambda i: ['Default'], field='TerminationPolicies')
    replacement_policy = argument.String(choices=['singleton', 'graceful'], default='graceful')

    tags = argument.ResourceList(
        AutoScalingGroupTag,
        serializer=serializers.List(serializers.Resource()),
        field='Tags',
        update=False,
    )

    account = argument.Resource(BaseAccount)


class WaitForHealthy(Action):

    @property
    def description(self):
        yield 'Wait for there to be {} healthy instance(s)'.format(
            self.resource.min_size,
        )

    def run(self):
        while True:
            asg = self.plan.object = self.plan.describe_object()
            if len([i for i in asg['Instances'] if i['LifecycleState'] == 'InService']) >= self.resource.min_size:
                return True
            time.sleep(5)


class ReplaceInstances(Action):

    scaling_processes = [
        'AlarmNotification',
        'AZRebalance',
        'ReplaceUnhealthy',
        'ScheduledActions',
    ]

    def __init__(self, plan, instance_ids):
        super(ReplaceInstances, self).__init__(plan)
        self.instance_ids = instance_ids
        self.desired_capacity = plan.object.get('DesiredCapacity', self.resource.min_size)

    @property
    def description(self):
        yield 'Replace stale instances'
        for instance_id in self.instance_ids:
            yield instance_id

    def suspend_processes(self):
        self.plan.client.suspend_processes(
            AutoScalingGroupName=self.resource.name,
            ScalingProcesses=self.scaling_processes,
        )

    def terminate_instance(self, instance_id):
        self.plan.echo('Terminating instance {}'.format(instance_id))
        self.plan.client.terminate_instance_in_auto_scaling_group(
            InstanceId=instance_id,
            ShouldDecrementDesiredCapacity=False,
        )

    def wait_for_healthy_elb(self, elb):
        self.plan.echo('Waiting for load balancer {} to report healthy'.format(elb))
        obj = self.runner.get_plan(elb)
        while True:
            result = obj.client.describe_instance_health(
                LoadBalancerName=obj.resource_id,
            )
            states = result.get('InstanceStates', [])
            if len(filter(lambda s: s['State'] != 'InService', states)) == 0:
                return True

            time.sleep(5)

    def wait_for_healthy_asg(self):
        self.plan.echo('Waiting for scaling group to become healthy')
        while True:
            asg = self.plan.describe_object()
            if self.desired_capacity == len([i for i in asg['Instances'] if i['LifecycleState'] == 'InService']):
                for elb in self.resource.load_balancers:
                    self.wait_for_healthy_elb(elb)
                return True
            time.sleep(5)

    def resume_processes(self):
        self.plan.client.resume_processes(
            AutoScalingGroupName=self.resource.name,
            ScalingProcesses=self.scaling_processes,
        )

    def run(self):
        self.plan.echo('Suspend autoscaling activities')
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
            self.plan.echo('Resuming autoscaling activities')
            self.resume_processes()

        # Make sure that our dependents have up to date intel on instances we
        # have just brought into service
        self.plan.object = self.plan.describe_object()


class GracefulReplacement(ReplaceInstances):

    def scale(self):
        self.plan.echo('Increasing scaling group capacity for node replacement')
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
        self.plan.echo('Restoring scaling group to original capacity')
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
    api_version = '2011-01-01'
    describe_action = 'describe_auto_scaling_groups'
    describe_envelope = 'AutoScalingGroups'
    key = 'AutoScalingGroupName'

    @cached_property
    def ec2_client(self):
        return self.session.create_client('ec2')

    def get_describe_filters(self):
        return {'AutoScalingGroupNames': [self.resource.name]}


class Apply(SimpleApply, Describe):

    create_action = 'create_auto_scaling_group'
    create_response = 'not-that-useful'
    update_action = 'update_auto_scaling_group'

    signature = (
        Present('name'),
        Present('min_size'),
        Present('max_size'),
        Present('launch_configuration'),
    )

    def update_tags(self):
        diff = serializers.Argument('tags').diff(
            self.runner,
            self.resource,
            self.object.get('Tags', []),
        )

        if not diff.matches():
            yield self.generic_action(
                ['Update tags'] + list(diff.lines()),
                self.client.create_or_update_tags,
                Tags=serializers.Argument('tags'),
            )

        to_delete = []
        for d in self.object.get('Tags', []):
            if d['Key'] not in (t.name for t in self.resource.tags):
                to_delete.append({
                    'ResourceId': self.resource.name,
                    'ResourceType': 'auto-scaling-group',
                    'Key': d['Key'],
                })

        if to_delete:
            yield self.generic_action(
                ['Delete stale tags'] + ['* ' + t['Key'] for t in to_delete],
                self.client.delete_tags,
                Tags=to_delete,
            )

    def update_object(self):
        for change in super(Apply, self).update_object():
            yield change

        for change in self.update_tags():
            yield change

        if self.resource.min_size and self.resource.min_size > 0:
            if len(self.object.get('Instances', [])) < self.resource.min_size:
                yield WaitForHealthy(self)

        launch_config_name = self.runner.get_plan(self.resource.launch_configuration).resource_id
        instances = []

        for instance in self.object.get('Instances', []):
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
        yield 'Scale down and wait for {} instances to terminate'.format(
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
            if len(asg.get('Instances', [])) == 0:
                break
            time.sleep(10)

        # Wait until any ASG activies have stopped
        while True:
            activities = self.plan.client.describe_scaling_activities(AutoScalingGroupName=self.resource.name)['Activities']
            if len(tuple(a for a in activities if a['StatusCode'] == 'InProgress')) == 0:
                break
            time.sleep(10)


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_auto_scaling_group'

    def destroy_object(self):
        yield TerminateASGInstances(self)
        for change in super(Destroy, self).destroy_object():
            yield change


class Instance(ssh.Instance):

    resource_name = 'random_asg_instance'
    input = AutoScalingGroup

    def get_instances(self, runner):
        plan = runner.get_plan(self.adapts)
        obj = plan.describe_object()
        if len(obj.get('Instances', [])) == 0:
            raise errors.ServiceNotReady('No instances currently running in group {}'.format(self.adapts))

        asg_inservice = list(filter(
            lambda x: x['LifecycleState'] == 'InService',
            obj.get('Instances', []),
        ))

        if len(asg_inservice) == 0:
            raise errors.ServiceNotReady('None of the instances in {} are in service'.format(self.adapts))

        reservations = plan.ec2_client.describe_instances(
            InstanceIds=[i['InstanceId'] for i in asg_inservice],
        ).get('Reservations', [])

        instances = []
        for reservation in reservations:
            instances.extend(reservation.get('Instances', []))

        if len(instances) == 0:
            raise errors.ServiceNotReady('No instances available in {}'.format(self.adapts))

        return instances

    def get_network_id(self, runner):
        instances = self.get_instances(runner)
        ids = set(i.get('VpcId') for i in instances)
        if len(ids) == 1:
            return tuple(ids)[0]

    def get_serializer(self, runner, **kwargs):
        instances = self.get_instances(runner)

        if getattr(self.parent, 'proxy', None) and self.parent.proxy.instance:
            if hasattr(self.parent.proxy.instance, 'get_network_id'):
                network = self.parent.proxy.instance.get_network_id(runner)
                possible = []
                for instance in instances:
                    if instance['VpcId'] != network:
                        continue
                    if 'PrivateIpAddress' not in instance:
                        continue
                    possible.append(instance['PrivateIpAddress'])
                if possible:
                    return serializers.Const(random.choice(possible))

        for instance in instances:
            possible = []
            for k in ('PublicDnsName', 'PublicIpAddress'):
                if k in instance and instance[k]:
                    possible.append(instance[k])
                    break
            if possible:
                return serializers.Const(random.choice(possible))

        raise errors.ServiceNotReady('No instances available in {} with ip address'.format(self.adapts))
