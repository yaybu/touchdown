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

from touchdown.core import argument, errors, resource, serializers
from touchdown.core.action import Action
from touchdown.core.plan import Plan

from . import IniFile


class Variable(resource.Resource):

    resource_name = 'variable'

    name = argument.String()
    retain_default = argument.Boolean(default=False)
    config = argument.Resource(IniFile)


class Describe(Plan):

    resource = Variable
    name = 'describe'

    def get_actions(self):
        try:
            val, user_set = self.runner.get_service(self.resource, 'get').execute()
        except KeyError:
            val = None
            user_set = False
        self.object = {
            'Value': val,
            'UserSet': user_set,
        }
        return []


class ApplyAction(Action):

    @property
    def description(self):
        yield 'Generate and store setting {!r}'.format(self.resource.name)

    def run(self):
        default = serializers.maybe(self.resource.default).render(
            self.runner, self.resource
        )
        self.runner.get_service(self.resource, 'set').execute(default)


class Apply(Plan):

    resource = Variable
    name = 'apply'
    apply_action = ApplyAction

    def get_actions(self):
        try:
            val, user_set = self.runner.get_service(self.resource, 'get').execute()
        except KeyError:
            user_set = False
        if not user_set and self.resource.retain_default:
            yield self.apply_action(self)


class Set(Plan):

    resource = Variable
    name = 'set'

    def from_string(self, value):
        return value

    def to_lines(self, value):
        return [value]

    def execute(self, value):
        conf = self.runner.get_service(self.resource.config, 'describe')
        if '.' not in self.resource.name:
            raise errors.Error('You didn\'t specify a section')
        conf.set(self.resource.name, '\n'.join(self.to_lines(value)))


class Get(Plan):

    resource = Variable
    name = 'get'

    def to_string(self, value):
        return str(value)

    def from_lines(self, value):
        assert len(value) == 1
        return value[0]

    def get_default_value(self):
        return serializers.maybe(self.resource.default).render(
            self.runner,
            self.resource,
        )

    def execute(self):
        conf = self.runner.get_service(self.resource.config, 'describe')
        if '.' not in self.resource.name:
            raise errors.Error('You didn\'t specify a section')
        try:
            value = conf.get(self.resource.name)
        except KeyError:
            value = None

        if not value:
            return self.get_default_value(), False

        return self.from_lines(value.splitlines()), True


class Refresh(Plan):

    resource = Variable
    name = 'refresh'

    def execute(self):
        setter = self.runner.get_service(self.resource, 'set')
        setter.execute(serializers.maybe(self.resource.default).render(
            self.runner,
            self.resource,
        ))


class VariableAsString(serializers.Serializer):

    def __init__(self, resource):
        self.resource = resource

    def render(self, runner, object):
        return runner.get_service(self.resource, 'get').execute()[0]

    def dependencies(self, object):
        return frozenset((self.resource, ))
