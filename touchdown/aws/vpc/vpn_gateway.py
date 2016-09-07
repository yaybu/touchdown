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
from touchdown.core.plan import Plan
from touchdown.core.resource import Resource

from ..common import SimpleApply, SimpleDescribe, SimpleDestroy, TagsMixin
from .vpc import VPC


class AttachmentStateWaiter(Action):

    def __init__(self, plan, target_state, error_states):
        super(AttachmentStateWaiter, self).__init__(plan)
        self.target_state = target_state
        self.error_states = error_states

    @property
    def description(self):
        yield 'Wait for gateway to enter state "{}"'.format(self.target_state)

    def check(self):
        status = self.plan.describe_object()
        for attachment in status.get('VpcAttachments', []):
            if attachment['State'] in self.error_states:
                raise errors.Error('Gateway in unexpected state {}'.format(attachment['State']))
            if attachment['State'] != self.target_state:
                return False
        return True

    def run(self):
        for i in range(60):
            if self.check():
                return
            time.sleep(5)
        raise errors.Error('Took too long for attachment to enter state {}'.format(self.target_state))


class VpnGateway(Resource):

    resource_name = 'vpn_gateway'

    name = argument.String(field='Name', group='tags')
    type = argument.String(default='ipsec.1', choices=['ipsec.1'], field='Type')
    availability_zone = argument.String(field='AvailabilityZone')
    tags = argument.Dict()
    vpc = argument.Resource(VPC)


class Describe(SimpleDescribe, Plan):

    resource = VpnGateway
    service_name = 'ec2'
    api_version = '2015-10-01'
    describe_action = 'describe_vpn_gateways'
    describe_envelope = 'VpnGateways'
    key = 'VpnGatewayId'

    def get_describe_filters(self):
        vpc = self.runner.get_plan(self.resource.vpc)
        if not vpc.resource_id:
            return None

        return {
            'Filters': [
                {'Name': 'tag:Name', 'Values': [self.resource.name]},
            ],
        }


class Apply(TagsMixin, SimpleApply, Describe):

    create_action = 'create_vpn_gateway'

    def update_object(self):
        for change in super(Apply, self).update_object():
            yield change

        attach = True
        wait = True

        if self.object:
            vpc = self.runner.get_plan(self.resource.vpc)
            for attachment in self.object.get('VpcAttachments', []):
                if attachment['VpcId'] == vpc.resource_id:
                    if attachment['State'] == 'attached':
                        wait = False
                        attach = False
                        break
                    elif attachment['State'] == 'attaching':
                        attach = False
                        break

        if attach:
            yield self.generic_action(
                'Attach gateway to vpc',
                self.client.attach_vpn_gateway,
                VpnGatewayId=serializers.Identifier(),
                VpcId=self.resource.vpc.identifier(),
            )

        if wait:
            yield AttachmentStateWaiter(self, 'attached', ['detached', 'detaching'])


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_vpn_gateway'

    def destroy_object(self):
        wait = False

        for attachment in self.object.get('VpcAttachments', []):
            if attachment['State'] == 'attached':
                yield self.generic_action(
                    'Detach gateway from vpc {}'.format(attachment['VpcId']),
                    self.client.detach_vpn_gateway,
                    VpnGatewayId=self.resource_id,
                    VpcId=attachment['VpcId'],
                )
                wait = True

            if attachment['State'] == 'detaching':
                wait = True

        if wait:
            yield AttachmentStateWaiter(self, 'detached', ['attached', 'attaching'])

        for change in super(Destroy, self).destroy_object():
            yield change
