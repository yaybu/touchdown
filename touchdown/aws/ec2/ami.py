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
try:
    from contextlib import ExitStack
except ImportError:
    from contextlib2 import ExitStack

from touchdown.core.action import Action
from touchdown.core.resource import Resource
from touchdown.core.plan import Plan
from touchdown.core import argument, errors, serializers

from touchdown.provisioner import Step
from touchdown import ssh

from ..account import BaseAccount
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy


class Image(Resource):

    resource_name = "image"
    immutable_tags = True

    name = argument.String(min=3, max=128, field="Name")
    description = argument.String(field="Description")

    source_ami = argument.String()

    username = argument.String()
    steps = argument.List(argument.Resource(Step))

    #architecture = argument.String(field="Architecture", default="x86_64", choices=["x86_64", "i386"])
    #kernel = argument.String(field="KernelId")
    #ramdisk = argument.String(field="RamdiskId")
    #root_device_name = argument.String(field="RootDeviceName")
    #virtualization_type = argument.String(choices=["paravirtual", "hvm"], field="VirtualizationType")
    #sriov_net_support = argument.String(choices=["simple"], field="SriovNetSupport")
    #location = argument.String()
    #snapshot_id = argument.String()

    launch_permissions = argument.List()

    tags = argument.Dict()

    account = argument.Resource(BaseAccount)


class BuildInstance(Action):

    @property
    def description(self):
        yield "Build new AMI '{}' from '{}'".format(self.resource.name, self.resource.source_ami)

    def create_security_group(self):
        self.plan.echo("Creating temporary security group")
        security_group = self.plan.client.create_security_group(
            GroupName="temporary-security-group",
            Description="Temporary security group",
        )
        self.stack.callback(self.destroy_security_group, security_group)

        self.plan.echo("Granting SSH access")
        self.plan.client.authorize_security_group_ingress(
            GroupId=security_group['GroupId'],
            IpProtocol="tcp",
            FromPort=22,
            ToPort=22,
            CidrIp="0.0.0.0/0",
        )

        return security_group

    def destroy_security_group(self, security_group):
        self.plan.echo("Deleting temproary security group")
        self.plan.client.delete_security_group(
            GroupId=security_group["GroupId"],
        )

    def create_keypair(self):
        self.plan.echo("Creating temporary keypair")
        keypair = self.plan.client.create_key_pair(
            KeyName="temporary-key-pair",
        )
        self.stack.callback(self.destroy_keypair, keypair)
        return keypair

    def destroy_keypair(self, keypair):
        self.plan.echo("Deleting temproary keypair")
        self.plan.client.delete_key_pair(
            KeyName=keypair["KeyName"],
        )

    def create_instance(self, keypair, security_group):
        self.plan.echo("Creating a source instance from {}".format(self.resource.source_ami))
        reservations = self.plan.client.run_instances(
            ImageId=self.resource.source_ami,
            InstanceType="m1.small",
            MaxCount=1,
            MinCount=1,
            KeyName=keypair['KeyName'],
            NetworkInterfaces=[{
                "DeviceIndex": 0,
                "AssociatePublicIpAddress": True,
                "Groups": [security_group['GroupId']],
            }],
        )

        if len(reservations.get("Instances", [])) == 0:
            raise errors.Error("No instances were started")
        elif len(reservations["Instances"]) > 1:
            raise errors.Error("Somehow multiple instances were started!?")

        instance = reservations["Instances"][0]

        self.stack.callback(self.terminate_instance, instance)

        self.plan.echo("Waiting for instance {} to boot...".format(instance["InstanceId"]))
        self.plan.client.get_waiter("instance_running").wait(InstanceIds=[instance["InstanceId"]])

        # We have to now get the info about the isntance again so we know
        # it's public ip address
        reservation = self.plan.client.describe_instances(
            InstanceIds=[instance["InstanceId"]]
        )['Reservations'][0]
        return reservation["Instances"][0]

    def deploy_instance(self, keypair, instance):
        cli = ssh.Client()

        cli.connect(
            hostname=instance['PublicIpAddress'],
            username=self.resource.username,
            pkey=ssh.private_key_from_string(keypair['KeyMaterial']),
            look_for_keys=False,
            #use_agent=False,
        )
        for step in self.resource.steps:
            cli.run_script(**serializers.Resource().render(self.runner, step))

    def terminate_instance(self, instance):
        self.plan.echo("Terminating instance")
        self.plan.client.terminate_instances(
            InstanceIds=[instance["InstanceId"]],
        )

        self.plan.echo("Waiting for instance to go away")
        self.plan.client.get_waiter("instance_terminated").wait(InstanceIds=[instance["InstanceId"]])

    def run(self):
        self.stack = ExitStack()
        with self.stack:
            keypair = self.create_keypair()
            security_group = self.create_security_group()
            instance = self.create_instance(keypair, security_group)

            self.plan.echo("Deploying instance")
            self.deploy_instance(keypair, instance)

            self.plan.echo("Creating image")
            self.plan.client.create_image(
                Name=self.resource.name,
                InstanceId=instance['InstanceId'],
            )

            self.plan.echo("Waiting for image to become available")
            # self.plan.client.get_waiter("ami_available").wait(ImageId=[image["ImageId"]])
            for i in range(20):
                self.plan.object = self.plan.describe_object()
                if self.plan.object.get("State", "pending") == "available":
                    self.plan.echo("Image '{}' built.".format(self.plan.object["ImageId"]))
                    return
                time.sleep(15)
            raise errors.Error("Image didn't become available")


class Describe(SimpleDescribe, Plan):

    resource = Image
    service_name = 'ec2'
    describe_action = "describe_images"
    describe_list_key = "Images"
    key = 'ImageId'

    def get_describe_filters(self):
        return {"Filters": [{"Name": "name", "Values": [self.resource.name]}]}


class Apply(SimpleApply, Describe):

    create_action = "create_image"
    create_response = "not-that-useful"

    def create_object(self):
        return BuildInstance(self)

    def update_object(self):
        for change in super(Apply, self).update_object():
            yield change

        description = ["Update who can launch this image"]

        remote_userids = []
        if self.object:
            results = self.client.describe_image_attribute(
                ImageId=self.object['ImageId'],
                Attribute="launchPermission",
            ).get("LaunchPermissions", [])
            remote_userids = [r['UserId'] for r in results]

        add = []
        for userid in self.resource.launch_permissions:
            if not userid in remote_userids:
                description.append("Add launch permission for '{}'".format(userid))
                add.append({"UserId": userid})

        remove = []
        for userid in remote_userids:
            if not userid in self.resource.launch_permissions:
                description.append("Remove launch permission for '{}'".format(userid))
                remove.append({"UserId": userid})

        if add or remove:
            yield self.generic_action(
                description,
                self.client.modify_image_attribute,
                ImageId=serializers.Identifier(),
                Attribute="launchPermission",
                LaunchPermission=dict(
                    Add=add,
                    Remove=remove,
                ),
            )


class Destroy(SimpleDestroy, Describe):

    destroy_action = "deregister_image"
