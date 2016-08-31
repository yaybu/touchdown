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

from touchdown.core import argument, serializers
from touchdown.core.plan import Plan
from touchdown.core.resource import Resource

from ..common import SimpleApply, SimpleDescribe, SimpleDestroy, TagsMixin
from .vpc import VPC


class InternetGateway(Resource):

    resource_name = 'internet_gateway'

    name = argument.String(field='Name', group='tags')
    tags = argument.Dict()
    vpc = argument.Resource(VPC)


class Describe(SimpleDescribe, Plan):

    resource = InternetGateway
    service_name = 'ec2'
    api_version = '2015-10-01'
    describe_action = 'describe_internet_gateways'
    describe_envelope = 'InternetGateways'
    key = 'InternetGatewayId'

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

    create_action = 'create_internet_gateway'

    def get_create_serializer(self):
        # As the create call takes *0* parameters, the serializers consider it
        # a 'FieldNotPresent' and break out.
        return serializers.Const({})

    def update_object(self):
        for change in super(Apply, self).update_object():
            yield change

        for attachment in self.object.get('Attachments', []):
            if attachment['VpcId'] == self.runner.get_plan(self.resource.vpc).resource_id:
                return

        yield self.generic_action(
            'Attach to vpc {}'.format(self.resource.vpc),
            self.client.attach_internet_gateway,
            InternetGatewayId=self.resource.identifier(),
            VpcId=self.resource.vpc.identifier(),
        )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_internet_gateway'

    def destroy_object(self):
        for attachment in self.object.get('Attachments', []):
            yield self.generic_action(
                'Detach from vpc {}'.format(attachment['VpcId']),
                self.client.detach_internet_gateway,
                InternetGatewayId=self.resource_id,
                VpcId=attachment['VpcId'],
            )

        for change in super(Destroy, self).destroy_object():
            yield change
