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

from touchdown.aws.vpc import Subnet
from touchdown.core import argument
from touchdown.core.plan import Plan
from touchdown.core.resource import Resource

from ..account import BaseAccount
from ..common import SimpleApply, SimpleDescribe, SimpleDestroy


class SubnetGroup(Resource):

    resource_name = 'db_subnet_group'

    name = argument.String(field='DBSubnetGroupName')
    description = argument.String(field='DBSubnetGroupDescription')
    subnets = argument.ResourceList(Subnet, field='SubnetIds', update=False)
    # tags = argument.Dict()

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = SubnetGroup
    service_name = 'rds'
    api_version = '2014-10-31'
    describe_action = 'describe_db_subnet_groups'
    describe_notfound_exception = 'DBSubnetGroupNotFoundFault'
    describe_envelope = 'DBSubnetGroups'
    key = 'DBSubnetGroupName'


class Apply(SimpleApply, Describe):

    create_action = 'create_db_subnet_group'
    update_action = 'modify_db_subnet_group'


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_db_subnet_group'
