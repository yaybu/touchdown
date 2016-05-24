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
from .ip_set import IpSet
from .waf import WafApply, WafDescribe, WafDestroy


class Match(Resource):
    """A match gives some context to a set. This class is expected to be
    subclassed for each type of match.

    """
    negated = argument.Boolean(field='Negated')


class IPMatch(Match):
    resource_name = "ip_match"

    match_type = argument.Serializer(serializer=serializers.Const("IPMatch"), field="Type")
    ip_set = argument.Resource(IpSet, field='DataId')


class Rule(Resource):

    name = argument.String(field='Name')
    metric_name = argument.String(field='MetricName')
    predicates = argument.ResourceList(
        Match,
        field='Predicates',
        create=False,
    )
    account = argument.Resource(BaseAccount)


class Describe(WafDescribe, Plan):

    resource = Rule
    service_name = 'waf'
    describe_action = "list_rules"
    describe_envelope = "Rules"
    annotate_action = "get_rule"
    key = 'RuleId'
    local_container = "rules"
    container_update_action = 'update_rule'
    container = 'Predicates'
    container_member = 'Predicate'


class Apply(WafApply, Describe):

    create_action = "create_rule"


class Destroy(WafDestroy, Describe):

    destroy_action = "delete_rule"
