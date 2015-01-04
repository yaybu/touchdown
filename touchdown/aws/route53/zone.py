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
from ..common import SimpleApply


# FIXME: Figure out how to pass comment

class HostedZone(Resource):

    """ A DNS zone hosted at Amazon Route53 """

    resource_name = "hosted_zone"

    name = argument.String(aws_field="Name")
    comment = argument.String()
    account = argument.Resource(AWS)


class Apply(SimpleApply, Target):

    resource = HostedZone
    service_name = 'route53'
    create_action = "create_hosted_zone"
    # update_action = "update_hosted_zone_comment"
    describe_action = "list_hosted_zones"
    describe_list_key = "HostedZone"
    key = 'HostedZoneId'

    def describe_object(self):
        zone_name = self.resource.name.rstrip(".") + "."
        paginator = self.client.get_paginator("list_hosted_zones")
        for page in paginator.paginate():
            for zone in page['HostedZones']:
                if zone['Name'] == zone_name:
                    return zone

    def get_create_args(self):
        args = {
            "CallerReference": str(uuid.uuid4()),
        }
        args.update(super(Apply, self).get_create_args())
        return args
