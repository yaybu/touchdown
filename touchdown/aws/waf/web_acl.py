# Copyright 2016 Isotoma Limited
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

from touchdown.aws.common import Resource
from touchdown.core import argument, serializers
from touchdown.core.plan import Plan, Present

from ..account import BaseAccount
from .rule import Rule
from .waf import WafApply, WafDescribe, WafDestroy


class ActivatedRule(Resource):

    resource_name = 'activated_rule'

    action = argument.String(
        field='Action',
        choices=['BLOCK', 'ALLOW', 'COUNT'],
        serializer=serializers.Dict(
            Type=serializers.String(),
        ),
    )
    priority = argument.Integer(field='Priority')
    rule = argument.Resource(Rule, field='RuleId')


class WebACL(Resource):

    resource_name = 'web_acl'

    name = argument.String(field='Name')
    metric_name = argument.String(field='MetricName')
    default_action = argument.String(
        field='DefaultAction',
        choices=['BLOCK', 'ALLOW', 'COUNT'],
        serializer=serializers.Dict(
            Type=serializers.String(),
        )
    )
    activated_rules = argument.ResourceList(
        ActivatedRule,
        field='ActivatedRules',
        create=False,
    )
    account = argument.Resource(BaseAccount)


class Describe(WafDescribe, Plan):

    resource = WebACL
    service_name = 'waf'
    api_version = '2015-08-24'
    describe_action = 'list_web_acls'
    describe_envelope = 'WebACLs'
    annotate_action = 'get_web_acl'
    key = 'WebACLId'
    container_update_action = 'update_web_acl'
    container = 'Rules'
    container_member = 'ActivatedRule'
    local_container = 'activated_rules'


class Apply(WafApply, Describe):

    create_action = 'create_web_acl'

    signature = (
        Present('name'),
        Present('metric_name'),
        Present('default_action'),
    )


class Destroy(WafDestroy, Describe):

    destroy_action = 'delete_web_acl'
