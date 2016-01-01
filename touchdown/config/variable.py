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


class Variable(resource.Resource):

    resource_name = "variable"

    name = argument.String()
    config = argument.Resource(IniFile)

    @property
    def value(self):
        return self.get_property("Value")


class Describe(Plan):

    resource = Variable
    name = "describe"

    def get_actions(self):
        self.object = {
            "Value": self.runner.get_service(self.resource, "get").execute(),
        }
        return []


class Set(Plan):

    resource = Variable
    name = "set"

    def to_lines(self, value):
        return [value]

    def execute(self, value):
        conf = self.runner.get_plan(self.resource.config)
        if "." not in self.resource.name:
            raise errors.Error("You didn't specify a section")
        section, name = self.resource.name.rsplit(".", 1)
        c = conf.read()
        if not c.has_section(section):
            c.add_section(section)
        c.set(section, name, "\n".join(self.to_lines(value)))
        conf.write(c)


class Get(Plan):

    resource = Variable
    name = "get"

    def from_lines(self, value):
        assert len(value) == 1
        return value[0]

    def execute(self):
        conf = self.runner.get_plan(self.resource.config)
        if "." not in self.resource.name:
            raise errors.Error("You didn't specify a section")
        section, name = self.resource.name.rsplit(".", 1)
        c = conf.read()
        try:
            return self.from_lines(c.get(section, name).splitlines())
        except configparser.NoSectionError:
            return self.resource.default
        except configparser.NoOptionError:
            return self.resource.default


class Refresh(Plan):

    resource = Variable
    name = "refresh"

    def execute(self):
        setter = self.runner.get_service(self.resource, "set")
        setter.execute(self.resource.default)
