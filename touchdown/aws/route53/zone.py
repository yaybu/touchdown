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

import uuid

from touchdown.core.resource import Resource
from touchdown.core.target import Target
from touchdown.core import argument

from ..account import AWS
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy
from ..vpc import VPC
from .. import serializers


class Record(Resource):

    resource_name = "record"

    name = argument.String(aws_field="Name")
    type = argument.String(aws_field="Type")
    values = argument.List(
        aws_field="ResourceRecords",
        aws_serializer=serializers.List(serializers.Dict(
            Value=serializers.Identity),
        ))
    ttl = argument.Integer(min=0, aws_field="TTL")

    set_identifier = argument.Integer(min=1, max=128, aws_field="SetIdentifier")
    #weight = argument.Integer(min=1, max=255, aws_field="Weight")
    #region = argument.String(aws_field="Region")
    #geo_location = argument.String(aws_field="GeoLocation")
    #failover = argument.String(choices=["PRIMARY", "SECONDARY"], aws_field="Failover")
    #alias_target = argument.Resource(aws_field="AliasTarget")
    #health_check = argument.Resource(aws_field="HealthCheckId")


class HostedZone(Resource):

    """ A DNS zone hosted at Amazon Route53 """

    resource_name = "hosted_zone"

    extra_serializers = {
        "CallerReference": serializers.Expression(lambda x, y: str(uuid.uuid4())),
    }

    name = argument.String(aws_field="Name")
    vpc = argument.Resource(VPC, aws_field="VPC")
    comment = argument.String(
        aws_field="HostedZoneConfig",
        aws_serializer=serializers.Dict(
            Comment=serializers.Identity(),
        ),
    )

    records = argument.ResourceList(Record)
    account = argument.Resource(AWS)


class Describe(SimpleDescribe, Target):

    resource = HostedZone
    service_name = 'route53'
    describe_action = "list_hosted_zones"
    describe_list_key = "HostedZone"
    key = 'Id'

    def describe_object(self):
        zone_name = self.resource.name.rstrip(".") + "."
        paginator = self.client.get_paginator("list_hosted_zones")
        for page in paginator.paginate():
            for zone in page['HostedZones']:
                if zone['Name'] == zone_name:
                    return zone


class Apply(SimpleApply, Describe):

    create_action = "create_hosted_zone"
    # update_action = "update_hosted_zone_comment"

    def get_create_args(self):
        args = {
            "CallerReference": str(uuid.uuid4()),
        }
        args.update(super(Apply, self).get_create_args())
        return args

    def _get_remote_records(self):
        if not self.object:
            return {}
        records = {}
        for record in self.client.list_resource_record_sets(HostedZoneId=self.resource_id)['ResourceRecordSets']:
            records[(record['Name'], record['Type'], record.get('SetIdentifier', ''))] = record
        return records

    def _get_local_records(self):
        records = {}
        for record in self.resource.records:
            records[(record.name, record.type, record.set_identifier)] = serializers.Resource().render(self.runner, record)
        return records

    def update_object(self):
        local = self._get_local_records()
        remote = self._get_remote_records()
        changes = []

        for key, record in local.items():
            if record != remote.get(key, {}):
                changes.append({"Action": "UPSERT", "ResourceRecordSet": record})

        for key, record in remote.items():
            if record != local.get(key, {}):
                changes.append({"Action": "DELETE", "ResourceRecordSet": record})

        if changes:
            yield self.generic_action(
                "Update resource record sets",
                self.client.change_resource_record_sets,
                None,
                serializers.Dict(
                    HostedZoneId=serializers.Identifier(),
                    ChangeBatch=serializers.Dict(
                        #Comment="",
                        Changes=serializers.Context(serializers.Const(changes), serializers.List()),
                    )
                ),
            )


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_hosted_zone"
