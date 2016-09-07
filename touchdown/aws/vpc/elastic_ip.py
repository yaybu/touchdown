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

from touchdown.config import String
from touchdown.core import argument, serializers
from touchdown.core.action import Action
from touchdown.core.plan import Plan, Present
from touchdown.core.resource import Resource

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy


class ElasticIp(Resource):

    resource_name = 'elastic_ip'

    name = argument.String()
    public_ip = argument.Resource(String)

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = ElasticIp
    service_name = 'ec2'
    api_version = '2015-10-01'
    describe_action = 'describe_addresses'
    describe_envelope = 'Addresses'
    key = 'PublicIp'

    signature = (
        Present('name'),
        Present('public_ip'),
    )

    def get_describe_filters(self):
        public_ip, _ = self.runner.get_service(self.resource.public_ip, 'get').execute()
        if not public_ip:
            return

        return {
            'Filters': [
                {'Name': 'public-ip', 'Values': [public_ip]},
            ]
        }


class NameAction(Action):

    @property
    def description(self):
        yield 'Store setting elastic ip as setting {!r}'.format(self.resource.public_ip.name)

    def run(self):
        self.runner.get_service(self.resource.public_ip, 'set').execute(
            self.plan.object['PublicIp']
        )


class Apply(SimpleApply, Describe):

    create_action = 'allocate_address'
    create_envelope = '@'
    create_response = 'full-description'

    def get_create_serializer(self):
        return serializers.Dict(
            Domain='vpc',
        )

    def name_object(self):
        yield NameAction(self)


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'release_address'

    def get_destroy_serializer(self):
        return serializers.Dict(
            AllocationId=serializers.Property('AllocationId'),
        )
