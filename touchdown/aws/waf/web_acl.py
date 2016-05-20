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
from touchdown.core.plan import Plan

from ..account import BaseAccount
from .waf import (
    WafApply,
    WafDescribe,
    WafDestroy,
)
from .ip_set import IPSet


class ActivatedRule(Resource):
    negated = argument.Boolean(field='Negated')


class WebACL(Resource):

    name = argument.String(field='Name')
    metric_name = argument.String(field='MetricName')
    default_action = argument.String(field='DefaultAction', choices=['BLOCK', 'ALLOW', 'COUNT'])
    activated_rules = argument.ResourceList(
        ActivatedRule,
        field='ActivatedRules',
        create=False,
    )
    account = argument.Resource(BaseAccount)


class Describe(WafDescribe, Plan):

    resource = WebACL
    service_name = 'waf'
    describe_action = "list_web_acls"
    describe_envelope = "WebACLSs"
    annotate_action = "get_web_acl"
    key = 'WebACLId'


class Apply(WafApply, Describe):

    create_action = "create_web_acl"

    local_children = "activated_rules"
    container_update_action = 'update_web_acl'
    container = 'Rules'
    container_member = 'ActivatedRule'

    def update_object(self):
        changes = []
        description = ["Update Web ACL"]

        for local in self.resource.predicates:
            for remote in self.object.get('Predicates', []):
                if local.matches(self.runner, remote):
                    break
            else:
                changes.append(serializers.Dict(**{
                    "Action": "INSERT",
                    "Predicate": local.serializer_with_kwargs(),
                }))
                description.append("Type => {}, Predicate={}, Action=INSERT".format(local.match_type, local.ip_set))

        for remote in self.object.get('Predicates', []):
            for local in self.resource.predicates:
                if local.matches(self.runner, remote):
                    break
            else:
                changes.append(serializers.Dict(**{
                    "Action": "DELETE",
                    "Predicate": remote,
                }))
                # TODO: consider doing a call here to a better
                # description for the deleted resource.
                description.append("Type => {}, Predicate={}, Action=DELETE".format(remote["Type"], remote["DataId"]))

        if changes:
            yield self.generic_action(
                description,
                self.client.update_web_acl,
                WebACLId=serializers.Identifier(),
                Updates=serializers.Context(serializers.Const(changes), serializers.List(serializers.SubSerializer())),
            )


class Destroy(WafDestroy, Describe):

    destroy_action = "delete_web_acl"
    container_update_action = 'update_web_acl'
    container = 'Rules'
    container_member = 'ActivatedRule'
