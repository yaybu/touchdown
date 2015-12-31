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

from six.moves import configparser

from touchdown.core.plan import Plan
from touchdown.core import argument, errors, resource

from . import IniFile


class String(resource.Resource):

    resource_name = "string"

    name = argument.String()
    default = argument.String()
    min = argument.String()
    max = argument.String()

    config = argument.Resource(IniFile)

    @property
    def value(self):
        return self.property("Value")


class Describe(Plan):

    resource = String
    name = "describe"

    def get_actions(self):
        self.object = {
            "Value": self.runner.get_service(self, "get").execute(),
        }
        return []


class Set(Plan):

    resource = String
    name = "set"

    def execute(self, value):
        conf = self.runner.get_plan(self.resource.config)
        if "." not in self.resource.name:
            raise errors.Error("You didn't specify a section")
        section, name = self.resource.name.rsplit(".", 1)
        c = conf.read()
        if not c.has_section(section):
            c.add_section(section)
        c.set(section, name, value)
        conf.write(c)


class Get(Plan):

    resource = String
    name = "get"

    def execute(self):
        conf = self.runner.get_plan(self.resource.config)
        if "." not in self.resource.name:
            raise errors.Error("You didn't specify a section")
        section, name = self.resource.name.rsplit(".", 1)
        c = conf.read()
        try:
            return c.get(section, name)
        except configparser.NoSectionError:
            return self.resource.default
        except configparser.NoOptionError:
            return self.resource.default


argument.String.register_adapter(String, lambda r: r.value)
