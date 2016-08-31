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

import time

from touchdown.core import argument, errors, serializers
from touchdown.core.action import Action
from touchdown.core.plan import Plan, Present
from touchdown.core.resource import Resource
from touchdown.core.utils import cached_property

from .. import route53
from ..account import BaseAccount
from ..acm import Certificate
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy
from ..iam import ServerCertificate
from ..s3 import Bucket
from ..vpc import SecurityGroup, Subnet


class Listener(Resource):

    resource_name = 'listener'

    protocol = argument.String(field='Protocol')
    port = argument.Integer(field='LoadBalancerPort')
    instance_protocol = argument.String(field='InstanceProtocol')
    instance_port = argument.Integer(field='InstancePort')
    ssl_certificate = argument.Resource(
        ServerCertificate,
        field='SSLCertificateId',
        serializer=serializers.Property('Arn'),
    )
    acm_certificate = argument.Resource(
        Certificate,
        field='SSLCertificiateId',
        serializer=serializers.Property('CertificateArn'),
    )


class HealthCheck(Resource):

    resource_name = 'health_check'
    dot_ignore = True

    interval = argument.Integer(field='Interval')
    check = argument.String(field='Target')
    healthy_threshold = argument.Integer(field='HealthyThreshold')
    unhealthy_threshold = argument.Integer(field='UnhealthyThreshold')
    timeout = argument.Integer(field='Timeout')


class LoadBalancer(Resource):

    resource_name = 'load_balancer'

    name = argument.String(field='LoadBalancerName')
    listeners = argument.ResourceList(
        Listener,
        field='Listeners',
        serializer=serializers.List(serializers.Resource()),
    )
    availability_zones = argument.List(field='AvailabilityZones')
    scheme = argument.String(choices=['internet-facing', 'private'], field='Scheme')
    subnets = argument.ResourceList(Subnet, field='Subnets')
    security_groups = argument.ResourceList(SecurityGroup, field='SecurityGroups')
    # tags = argument.Dict()

    health_check = argument.Resource(HealthCheck, serializer=serializers.Resource())

    idle_timeout = argument.Integer(
        default=30,
        field='ConnectionSettings',
        group='attributes',
        serializer=serializers.Dict(
            IdleTimeout=serializers.Identity(),
        ),
    )

    connection_draining = argument.Integer(
        default=0,
        field='ConnectionDraining',
        group='attributes',
        serializer=serializers.Dict(
            Enabled=serializers.Expression(lambda runner, object: object > 0),
            Timeout=serializers.Identity(),
        )
    )

    cross_zone_load_balancing = argument.Boolean(
        default=True,
        field='CrossZoneLoadBalancing',
        group='attributes',
        serializer=serializers.Dict(
            Enabled=serializers.Identity(),
        )
    )

    access_log = argument.Resource(
        Bucket,
        field='AccessLog',
        group='attributes',
        serializer=serializers.Dict(
            Enabled=serializers.Expression(lambda runner, object: object is not None),
            S3BucketName=serializers.Identifier(),
        )
    )
    # FIXME Support EmitInterval and S3BucketPrefix

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = LoadBalancer
    service_name = 'elb'
    api_version = '2012-06-01'
    describe_action = 'describe_load_balancers'
    describe_envelope = 'LoadBalancerDescriptions'
    describe_notfound_exception = 'LoadBalancerNotFound'
    key = 'LoadBalancerName'

    def get_describe_filters(self):
        return {'LoadBalancerNames': [self.resource.name]}

    def annotate_object(self, obj):
        obj['LoadBalancerAttributes'] = self.client.describe_load_balancer_attributes(
            LoadBalancerName=obj['LoadBalancerName'],
        )['LoadBalancerAttributes']
        return obj


class Apply(SimpleApply, Describe):

    create_action = 'create_load_balancer'
    create_response = 'not-that-useful'

    retryable = {
        # 'Server Certificate not found for the key: .*'
        'CertificateNotFound': [],
    }

    signature = [
        Present('name'),
        Present('listeners'),
    ]

    def update_attributes(self):
        diff = self.resource.diff(
            self.runner,
            self.object.get('LoadBalancerAttributes', {}),
            group='attributes',
        )
        if not diff.matches():
            yield self.generic_action(
                ['Configure attributes'] + list(diff.lines()),
                self.client.modify_load_balancer_attributes,
                LoadBalancerName=serializers.Identifier(),
                LoadBalancerAttributes=serializers.Resource(group='attributes'),
            )

    def update_health_check(self):
        if not self.object and self.resource.health_check:
            yield self.generic_action(
                'Configure health check',
                self.client.configure_health_check,
                LoadBalancerName=self.resource.name,
                HealthCheck=serializers.Argument('health_check'),
            )

    def update_object(self):
        for action in super(Apply, self).update_object():
            yield action
        for action in self.update_attributes():
            yield action
        for action in self.update_health_check():
            yield action


class WaitForNetworkInterfaces(Action):

    description = ['Wait for network interfaces to be released']

    def run(self):
        description = 'ELB {}'.format(self.plan.resource.name)
        for i in range(120):
            interfaces = self.plan.ec2_client.describe_network_interfaces(
                Filters=[
                    {'Name': 'description', 'Values': [description]},
                ]
            ).get('NetworkInterfaces', [])

            if len(interfaces) == 0:
                return

            time.sleep(1)

        raise errors.Error(
            'Load balancer {} still hanging around in Elastic Network Interfaces after deletion for over 2 minutes.'.format(
                self.plan.resource_id,
            )
        )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_load_balancer'

    @cached_property
    def ec2_client(self):
        return self.session.create_client('ec2')

    def destroy_object(self):
        for change in super(Destroy, self).destroy_object():
            yield change
        yield WaitForNetworkInterfaces(self)


class AliasTarget(route53.AliasTarget):

    ''' Adapts a LoadBalancer into a AliasTarget '''

    resource_name = 'load_balancer_alias_target'

    load_balancer = argument.Resource(
        LoadBalancer,
        field='DNSName',
        serializer=serializers.Context(
            serializers.Property('CanonicalHostedZoneName'),
            serializers.Expression(lambda r, o: route53._normalize(o)),
        ),
    )

    hosted_zone_id = argument.Serializer(
        field='HostedZoneId',
        serializer=serializers.Context(
            serializers.Expression(lambda r, o: o.load_balancer),
            serializers.Property('CanonicalHostedZoneNameID'),
        )
    )

    evaluate_target_health = argument.Boolean(
        field='EvaluateTargetHealth',
        default=False,
    )

    @classmethod
    def clean(cls, value):
        if isinstance(value, LoadBalancer):
            return super(AliasTarget, cls).clean({'load_balancer': value})
        return super(AliasTarget, cls).clean(value)
