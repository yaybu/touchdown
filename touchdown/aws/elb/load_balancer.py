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
from touchdown.core.target import Target, Present
from touchdown.core import argument, serializers

from ..account import Account
from ..iam import ServerCertificate
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy
from ..vpc import Subnet, SecurityGroup


class Listener(Resource):

    resource_name = "listener"

    protocol = argument.String(filed="Protocol")
    port = argument.Integer(field="LoadBalancerPort")
    instance_protocol = argument.String(field="InstanceProtocol")
    instance_port = argument.Integer(field="InstancePort")
    ssl_certificate = argument.Resource(
        ServerCertificate,
        field="SSLCertificiateId",
        serializer=serializers.Property("Arn"),
    )


class HealthCheck(Resource):

    resource_name = "health_check"
    dot_ignore = True

    interval = argument.Integer(field="Interval")
    target = argument.String(field="Target")
    healthy_threshold = argument.Integer(field="HealthyThreshold")
    unhealthy_threshold = argument.Integer(field="UnhealthyThreshold")
    timeout = argument.Integer(field="Timeout")


class LoadBalancer(Resource):

    resource_name = "load_balancer"

    name = argument.String(field="LoadBalancerName")
    listeners = argument.ResourceList(
        Listener,
        field="Listeners",
        serializers=serializers.List(serializers.Resource()),
    )
    availability_zones = argument.List(field="AvailabilityZones")
    scheme = argument.String(choices=["internet-facing", "private"], field="Scheme")
    subnets = argument.ResourceList(Subnet, field="Subnets")
    security_groups = argument.ResourceList(SecurityGroup, field="SecurityGroups")
    # tags = argument.Dict()

    health_check = argument.Resource(HealthCheck)

    account = argument.Resource(Account)


class Describe(SimpleDescribe, Target):

    resource = LoadBalancer
    service_name = 'elb'
    describe_action = "describe_load_balancers"
    describe_list_key = "LoadBalancerDescriptions"
    key = 'LoadBalancerName'

    def get_describe_filters(self):
        return {"LoadBalancerNames": [self.resource.name]}


class Apply(SimpleApply, Describe):

    create_action = "create_load_balancer"

    signature = [
        Present('name'),
        Present('listeners'),
    ]

    def update_object(self):
        for action in super(Apply, self).update_object():
            yield action

        if not self.object and self.health_check:
            yield self.generic_action(
                "Configure health check",
                self.client.configure_health_check,
                LoadBalancerName=self.resource.name,
                HealthCheck=serializers.Context(
                    serializers.Const(self.health_check),
                    serializers.Resource(),
                ),
            )


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_load_balancer"
