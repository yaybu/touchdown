# Copyright 2014-2015 Isotoma Limited
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

from touchdown.core import argument, resource, serializers


class KeyFilterRule(resource.Resource):

    resource_name = 'filter_rule'

    name = argument.String(field='Name', choices=['prefix', 'suffix'])
    value = argument.String(field='Value')


class NotificationConfiguration(resource.Resource):

    resource_name = 'notification_configuration'

    name = argument.String(field='Id')
    events = argument.List(argument.String(
        choices=[
            's3:ReducedRedundancyLostObject',
            's3:ObjectCreated:*',
            's3:ObjectCreated:Put',
            's3:ObjectCreated:Post',
            's3:ObjectCreated:Copy',
            's3:ObjectCreated:CompleteMultipartUpload',
            's3:ObjectRemoved:*',
            's3:ObjectRemoved:Delete',
            's3:ObjectRemoved:DeleteMarkerCreated',
        ],
    ), field='Events')

    filters = argument.ResourceList(
        KeyFilterRule,
        field='Filter',
        serializer=serializers.Dict(
            Key=serializers.Dict(
                FilterRules=serializers.List(serializers.Resource()),
            ),
        ),
    )
