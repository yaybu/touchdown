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

from touchdown.core.resource import Resource
from touchdown.core.target import Target
from touchdown.core import argument

from touchdown.aws.vpc import Subnet

from ..account import AWS
from ..common import SimpleApply


class SubnetGroup(Resource):

    resource_name = "cache_subnet_group"

    name = argument.String(aws_field="CacheSubnetGroupName")
    description = argument.String(aws_field="CacheSubnetGroupDescription")
    subnets = argument.ResourceList(Subnet, aws_field="SubnetIds")
    # tags = argument.Dict()

    account = argument.Resource(AWS)


class Apply(SimpleApply, Target):

    resource = SubnetGroup
    service_name = 'elasticache'
    create_action = "create_cache_subnet_group"
    update_action = "modify_cache_subnet_group"
    describe_action = "describe_cache_subnet_groups"
    describe_list_key = "CacheSubnetGroups"
    key = 'CacheSubnetGroupName'
