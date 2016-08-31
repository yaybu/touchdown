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

from touchdown.core import argument
from touchdown.core.plan import Plan

from ..account import BaseAccount
from ..common import Resource, SimpleApply, SimpleDescribe, SimpleDestroy


class LogGroup(Resource):

    resource_name = 'log_group'

    name = argument.String(min=1, max=512, field='logGroupName')
    retention = argument.Integer(
        default=0,
        choices=[
            0, 1, 3, 5, 7, 14, 30, 60, 90, 120, 150,
            180, 365, 400, 545, 731, 1827, 3653
        ],
    )

    account = argument.Resource(BaseAccount)


class Describe(SimpleDescribe, Plan):

    resource = LogGroup
    service_name = 'logs'
    api_version = '2014-03-28'
    describe_action = 'describe_log_groups'
    describe_envelope = 'logGroups'
    key = 'logGroupName'

    def get_describe_filters(self):
        return {'logGroupNamePrefix': self.resource.name}


class Apply(SimpleApply, Describe):

    create_action = 'create_log_group'
    create_response = 'nothing-useful'

    def update_object(self):
        for change in super(Apply, self).update_object():
            yield change

        if self.object.get('retentionInDays', 0) != self.resource.retention:
            yield self.generic_action(
                'Set log group retention to {} days'.format(
                    self.resource.retention
                ),
                self.client.put_retention_policy,
                logGroupName=self.resource.name,
                retentionInDays=self.resource.retention,
            )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_log_group'
