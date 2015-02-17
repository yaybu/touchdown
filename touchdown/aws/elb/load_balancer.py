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
from touchdown.core.plan import Plan, Present
from touchdown.core import argument, serializers

from ..account import Account
from ..iam import ServerCertificate
from ..s3 import Bucket
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy
from ..vpc import Subnet, SecurityGroup
from .. import route53


class Listener(Resource):

    resource_name = "listener"

    protocol = argument.String(field="Protocol")
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
    check = argument.String(field="Target")
    healthy_threshold = argument.Integer(field="HealthyThreshold")
    unhealthy_threshold = argument.Integer(field="UnhealthyThreshold")
    timeout = argument.Integer(field="Timeout")


class Attributes(Resource):

    resource_name = "attributes"
    dot_ignore = True

    idle_timeout = argument.Integer(
        default=30,
        field="ConnectionSettings",
        serializer=serializers.Dict(
            IdleTimeout=serializers.Identity(),
        ),
    )

    connection_draining = argument.Integer(
        default=0,
        field="ConnectionDraining",
        serializer=serializers.Dict(
            Enabled=serializers.Expression(lambda runner, object: object > 0),
            Timeout=serializers.Identity(),
        )
    )

    cross_zone_load_balancing = argument.Boolean(
        default=True,
        field="CrossZoneLoadBalancing",
        serializer=serializers.Dict(
            Enabled=serializers.Identity(),
        )
    )

    access_log = argument.Resource(
        Bucket,
        field="AccessLog",
        serializer=serializers.Dict(
            Enabled=serializers.Expression(lambda runner, object: object is not None),
            S3BucketName=serializers.Identifier(),
        )
    )
    # FIXME Support EmitInterval and S3BucketPrefix


class LoadBalancer(Resource):

    resource_name = "load_balancer"

    name = argument.String(field="LoadBalancerName")
    listeners = argument.ResourceList(
        Listener,
        field="Listeners",
        serializer=serializers.List(serializers.Resource()),
    )
    availability_zones = argument.List(field="AvailabilityZones")
    scheme = argument.String(choices=["internet-facing", "private"], field="Scheme")
    subnets = argument.ResourceList(Subnet, field="Subnets")
    security_groups = argument.ResourceList(SecurityGroup, field="SecurityGroups")
    # tags = argument.Dict()

    health_check = argument.Resource(HealthCheck)
    attributes = argument.Resource(Attributes)

    account = argument.Resource(Account)


class Describe(SimpleDescribe, Plan):

    resource = LoadBalancer
    service_name = 'elb'
    describe_action = "describe_load_balancers"
    describe_envelope = "LoadBalancerDescriptions"
    describe_notfound_exception = "LoadBalancerNotFound"
    key = 'LoadBalancerName'

    def get_describe_filters(self):
        return {"LoadBalancerNames": [self.resource.name]}


class Apply(SimpleApply, Describe):

    create_action = "create_load_balancer"
    create_response = "not-that-useful"

    signature = [
        Present('name'),
        Present('listeners'),
    ]

    def update_attributes(self):
        if not self.resource.attributes:
            return

        a = self.resource.attributes

        changed = False
        if not self.object:
            changed = True
        else:
            attributes = self.client.describe_load_balancer_attributes(
                LoadBalancerName=self.resource_id
            )['LoadBalancerAttributes']

            if attributes['ConnectionSettings']['IdleTimeout'] != a.idle_timeout:
                changed = True
            if attributes['ConnectionDraining']['Timeout'] != a.connection_draining:
                changed = True
            if attributes['CrossZoneLoadBalancing']['Enabled'] != a.cross_zone_load_balancing:
                changed = True
            if attributes['AccessLog'].get('S3BucketName', None) != a.access_log:
                changed = True

        if changed:
            yield self.generic_action(
                "Configure attributes",
                self.client.modify_load_balancer_attributes,
                LoadBalancerName=serializers.Identifier(),
                LoadBalancerAttributes=serializers.Context(
                    serializers.Const(a),
                    serializers.Resource()
                ),
            )

    def update_health_check(self):
        if not self.object and self.resource.health_check:
            yield self.generic_action(
                "Configure health check",
                self.client.configure_health_check,
                LoadBalancerName=self.resource.name,
                HealthCheck=serializers.Context(
                    serializers.Const(self.resource.health_check),
                    serializers.Resource(),
                ),
            )

    def update_object(self):
        for action in super(Apply, self).update_object():
            yield action
        for action in self.update_attributes():
            yield action
        for action in self.update_health_check():
            yield action


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_load_balancer"
    waiter = "load_balancer_deleted"


class AliasTarget(route53.AliasTarget):

    """ Adapts a LoadBalancer into a AliasTarget """

    input = LoadBalancer

    def get_serializer(self, runner, **kwargs):
        return serializers.Context(
            serializers.Const(self.adapts),
            serializers.Dict(
                DNSName=serializers.Context(
                    serializers.Property("CanonicalHostedZoneName"),
                    serializers.Expression(lambda r, o: route53._normalize(o)),
                ),
                HostedZoneId=serializers.Property("CanonicalHostedZoneNameID"),
                EvaluateTargetHealth=False,
            )
        )
