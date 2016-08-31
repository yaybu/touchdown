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
from .waf import WafApply, WafDescribe, WafDestroy


class ByteMatchTuple(Resource):

    resource_name = 'byte_match_tuple'

    field = argument.String(
        field='Type',
        group='FieldToMatch',
        choices=['URI', 'QUERY_STRING', 'HEADER', 'METHOD', 'BODY'],
    )

    header = argument.String(
        field='Data',
        group='FieldToMatch',
    )

    _field_to_match = argument.Serializer(
        field='FieldToMatch',
        serializer=serializers.Resource(group='FieldToMatch'),
    )

    transformation = argument.String(
        field='TextTransformation',
        default='NONE',
        choices=[
            'CMD_LINE',
            'COMPRESS_WHITE_SPACE',
            'HTML_ENTITY_DECODE',
            'LOWERCASE',
            'URL_DECODE',
            'NONE',
        ],
    )

    position = argument.String(
        field='PositionalConstraint',
        default='EXACTLY',
        choices=[
            'CONTAINS',
            'CONTAINS_WORD',
            'EXACTLY',
            'STARTS_WITH',
            'ENDS_WITH',
        ],
    )

    target = argument.String(
        field='TargetString',
        min=1,
        max=50,
    )


class ByteMatchSet(Resource):

    resource_name = 'byte_match_set'

    name = argument.String(field='Name')
    byte_matches = argument.ResourceList(
        ByteMatchTuple,
        field='ByteMatchTuple',
        create=False,
        serializer=serializers.List(serializers.Resource()),
    )
    account = argument.Resource(BaseAccount)


class Describe(WafDescribe, Plan):

    resource = ByteMatchSet
    service_name = 'waf'
    api_version = '2015-08-24'
    describe_action = 'list_byte_match_sets'
    describe_envelope = 'ByteMatchSets'
    annotate_action = 'get_byte_match_set'
    key = 'ByteMatchSetId'
    local_container = 'byte_matches'
    container_update_action = 'update_byte_match_set'
    container = 'ByteMatchTuples'
    container_member = 'ByteMatchTuple'


class Apply(WafApply, Describe):

    create_action = 'create_byte_match_set'


class Destroy(WafDestroy, Describe):

    destroy_action = 'delete_byte_match_set'
