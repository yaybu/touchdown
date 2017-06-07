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

from touchdown import ssh
from touchdown.aws.ec2 import KeyPair
from touchdown.aws.iam import InstanceProfile
from touchdown.aws.vpc import SecurityGroup, Subnet
from touchdown.core import argument, errors, serializers
from touchdown.core.plan import Plan, Present
from touchdown.core.resource import Resource

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy


class BlockDevice(Resource):

    resource_name = 'block_device'

    virtual_name = argument.String(field='VirtualName')
    device_name = argument.String(field='DeviceName')
    disabled = argument.Boolean(
        field='NoDevice',
        serializer=serializers.Const(''),
    )


class NetworkInterface(Resource):

    resource_name = 'network_interface'

    public = argument.Boolean(default=False, field='AssociatePublicIpAddress')
    security_groups = argument.ResourceList(SecurityGroup, field='Groups')


class Instance(Resource):

    resource_name = 'ec2_instance'

    name = argument.String(min=3, max=128, field='Name', group='tags')
    ami = argument.String(field='ImageId')
    instance_type = argument.String(field='InstanceType')
    key_pair = argument.Resource(KeyPair, field='KeyName')
    subnet = argument.Resource(Subnet, field='SubnetId')
    instance_profile = argument.Resource(
        InstanceProfile,
        field='IamInstanceProfile',
        serializer=serializers.Dict(
            Name=serializers.Property('InstanceProfileName')
        )
    )

    user_data = argument.String(field='UserData')

    network_interfaces = argument.ResourceList(
        NetworkInterface,
        field='NetworkInterfaces',
    )

    block_devices = argument.ResourceList(
        BlockDevice,
        field='BlockDeviceMappings',
        serializer=serializers.List(serializers.Resource()),
    )

    security_groups = argument.ResourceList(SecurityGroup, field='SecurityGroupIds')

    tags = argument.Dict()

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = Instance
    service_name = 'ec2'
    api_version = '2015-10-01'
    describe_action = 'describe_instances'
    describe_envelope = 'Reservations[].Instances[]'
    key = 'InstanceId'

    def get_describe_filters(self):
        return {
            'Filters': [
                {'Name': 'tag:Name', 'Values': [self.resource.name]},
                {'Name': 'instance-state-name', 'Values': [
                    'pending', 'running', 'shutting-down', ' stopping', 'stopped'
                ]},
            ]
        }


class Apply(SimpleApply, Describe):

    create_action = 'run_instances'
    create_envelope = 'Instances[0]'
    # create_response = 'id-only'
    waiter = 'instance_running'

    signature = (
        Present('name'),
    )

    def get_create_serializer(self):
        return serializers.Resource(
            MaxCount=1,
            MinCount=1,
        )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'terminate_instances'
    waiter = 'instance_terminated'

    def get_destroy_serializer(self):
        return serializers.Dict(
            InstanceIds=serializers.ListOfOne(serializers.Property('InstanceId')),
        )


class SSHInstance(ssh.Instance):

    resource_name = 'ec2_instance'
    input = Instance

    def get_network_id(self, runner):
        # FIXME: We can save on some steps if we only do this once
        obj = runner.get_plan(self.adapts).describe_object()
        return obj.get('VpcId', None)

    def get_serializer(self, runner, **kwargs):
        obj = runner.get_plan(self.adapts).describe_object()

        if getattr(self.parent, 'proxy', None) and self.parent.proxy.instance:
            if hasattr(self.parent.proxy.instance, 'get_network_id'):
                network = self.parent.proxy.instance.get_network_id(runner)
                if network == self.get_network_id(runner):
                    return serializers.Const(obj['PrivateIpAddress'])

        if obj.get('PublicDnsName', ''):
            return serializers.Const(obj['PublicDnsName'])

        if obj.get('PublicIpAddress', ''):
            return serializers.Const(obj['PublicIpAddress'])

        raise errors.Error('Instance {} not available'.format(self.adapts))
