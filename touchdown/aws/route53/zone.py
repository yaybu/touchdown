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

import uuid

from touchdown.core import argument, serializers
from touchdown.core.plan import Plan

from ..account import BaseAccount
from ..common import Resource, SimpleApply, SimpleDescribe, SimpleDestroy
from ..vpc import VPC
from .alias_target import AliasTarget


def _normalize(dns_name):
    '''
    The Amazon Route53 API silently accepts 'foo.com' as a dns record, but
    internally that becomes 'foo.com.'. In order to match records we need to do
    the same.
    '''
    return dns_name.rstrip('.') + '.'


class Record(Resource):

    resource_name = 'record'

    name = argument.String(field='Name')
    type = argument.String(field='Type')
    values = argument.List(
        field='ResourceRecords',
        serializer=serializers.List(serializers.Dict(
            Value=serializers.Identity(),
        ), skip_empty=True)
    )
    ttl = argument.Integer(min=0, field='TTL')

    set_identifier = argument.Integer(min=1, max=128, field='SetIdentifier')

    alias = argument.Resource(
        AliasTarget,
        field='AliasTarget',
        serializer=serializers.Resource(),
    )

    def clean_name(self, name):
        return _normalize(name)

    # weight = argument.Integer(min=1, max=255, field='Weight')
    # region = argument.String(field='Region')
    # geo_location = argument.String(field='GeoLocation')
    # failover = argument.String(choices=['PRIMARY', 'SECONDARY'], field='Failover')
    # health_check = argument.Resource(field='HealthCheckId')


class HostedZone(Resource):

    ''' A DNS zone hosted at Amazon Route53 '''

    resource_name = 'hosted_zone'

    extra_serializers = {
        'CallerReference': serializers.Expression(lambda x, y: str(uuid.uuid4())),
    }

    name = argument.String(field='Name')
    vpc = argument.Resource(VPC, field='VPC')
    comment = argument.String(
        field='HostedZoneConfig',
        serializer=serializers.Dict(
            Comment=serializers.Identity(),
        ),
    )

    records = argument.ResourceList(Record)

    shared = argument.Boolean()
    ''' If a hosted zone is shared then it won't be destroyed and DNS records will never be deleted '''

    account = argument.Resource(BaseAccount)

    def clean_name(self, name):
        return _normalize(name)


class Describe(SimpleDescribe, Plan):

    resource = HostedZone
    service_name = 'route53'
    api_version = '2013-04-01'
    describe_action = 'list_hosted_zones'
    describe_envelope = 'HostedZones'
    describe_filters = {}
    key = 'Id'

    def describe_object_matches(self, zone):
        return zone['Name'] == self.resource.name


class Apply(SimpleApply, Describe):

    create_action = 'create_hosted_zone'
    create_response = 'not-that-useful'
    # update_action = 'update_hosted_zone_comment'

    def get_remote_records(self):
        if not self.resource_id:
            return

        # Retrieve all DNS records associated with this hosted zone
        # Ignore SOA and NS records for the top level domain
        for record in self.client.list_resource_record_sets(HostedZoneId=self.resource_id)['ResourceRecordSets']:
            if record['Type'] in ('SOA', 'NS') and record['Name'] == self.resource.name:
                continue
            yield record

    def update_object(self):
        changes = []
        description = ['Update hosted zone records']

        remote_records = list(self.get_remote_records())
        for local in self.resource.records:
            for remote in remote_records:
                if local.matches(self.runner, remote):
                    break
            else:
                changes.append(serializers.Dict(
                    Action='UPSERT',
                    ResourceRecordSet=local.serializer_with_kwargs(),
                ))
                description.append('Name => {}, Type={}, Action=UPSERT'.format(local.name, local.type))

        if not self.resource.shared:
            for remote in remote_records:
                for local in self.resource.records:
                    if remote['Name'] != local.name:
                        continue
                    if remote['Type'] != local.type:
                        continue
                    if remote.get('SetIdentifier', None) != local.set_identifier:
                        continue
                    break
                else:
                    changes.append(serializers.Const({'Action': 'DELETE', 'ResourceRecordSet': remote}))
                    description.append('Name => {}, Type={}, Action=DELETE'.format(remote['Name'], remote['Type']))

        if changes:
            yield self.generic_action(
                description,
                self.client.change_resource_record_sets,
                serializers.Dict(
                    HostedZoneId=serializers.Identifier(),
                    ChangeBatch=serializers.Dict(
                        Changes=serializers.Context(serializers.Const(changes), serializers.List(serializers.SubSerializer())),
                    )
                ),
            )


class Destroy(SimpleDestroy, Describe):

    destroy_action = 'delete_hosted_zone'

    def destroy_object(self):
        if not self.resource.shared:
            for action in super(Destroy, self).destroy_object():
                yield action
