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
from touchdown.core.action import Action
from touchdown.core import argument, errors

from ..account import AWS


class HostedZone(Resource):

    """ A DNS zone hosted at Amazon Route53 """

    resource_name = "hosted_zone"

    name = argument.String()
    comment = argument.String()
    account = argument.Resource(AWS)


class AddHostedZone(Action):

    @property
    def description(self):
        yield "Add hosted zone '{}'".format(self.resource.name)

    def run(self):
        self.target.client.create_hosted_zone(
            CallerReference=str(uuid.uuid4()),
            Name=self.resource.name,
            HostedZoneConfig={
                "Comment": self.resource.comment,
            }
        )


class UpdateHostedZoneComment(Action):

    @property
    def description(self):
        yield "Change zone comment to '{}'".format(self.resource.comment)

    def __init__(self, runner, target, zone_id):
        super(UpdateHostedZoneComment, self).__init__(runner, target)
        self.zone_id = zone_id

    def run(self):
        self.target.client.update_hosted_zone_comment(
            Id=self.zone_id,
            Comment=self.resource.comment,
        )


class Apply(Target):

    name = "apply"
    resource = HostedZone
    default = True

    def get_zone(self):
        zone_name = self.resource.name.rstrip(".") + "."
        paginator = self.target.client.get_paginator("list_hosted_zones")
        for page in paginator.paginate():
            for zone in page['HostedZones']:
                if zone['Name'] == zone_name:
                    return zone

    def get_actions(self, runner):
        account = runner.get_target(self.resource.account)
        self.client = account.get_client('route53')

        zone = self.get_zone()
        if zone:
            if zone['Config'].get('Comment', '') != self.resource.comment:
                yield UpdateHostedZoneComment(self, zone['Id'])
        else:
            yield AddHostedZone(self)
