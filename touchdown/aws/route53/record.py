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

from touchdown.core.resource import Resource
from touchdown.core.target import Target
from touchdown.core.action import Action
from touchdown.core import argument

from .route53 import Route53Mixin
from .zone import Zone


class Record(Resource):
    resource_name = "record"

    name = argument.String()
    record_type = argument.String()
    data = argument.String()
    zone = argument.Resource(Zone)


class AddRecord(Action):

    @property
    def description(self):
        yield "Add {} to hosted zone".format(self.resource.name)

    def run(self):
        print "Adding record..."


class Apply(Target, Route53Mixin):
    name = "apply"
    resource = Record
    default = True

    def get_actions(self, runner):
        return [AddRecord(self)]
