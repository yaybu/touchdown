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
from touchdown.core import argument

from ..account import Account
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy
from ..vpc import Subnet, SecurityGroup


class LoadBalancer(Resource):

    resource_name = "load_balancer"

    name = argument.String(field="LoadBalancerName")
    listeners = argument.List(field="Listeners")
    availability_zones = argument.List(field="AvailabilityZones")
    scheme = argument.String(field="Scheme")
    subnets = argument.ResourceList(Subnet, field="Subnets")
    security_groups = argument.ResourceList(SecurityGroup, field="SecurityGroups")
    # tags = argument.Dict()

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


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_load_balancer"
