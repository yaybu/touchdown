# Copyright 2016 Isotoma Limited
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

from touchdown.core import argument, plan, resource
from touchdown.core.action import Action

from . import ip_allocations, variable


class Allocation(resource.Resource):

    resource_name = 'ip_allocation'
    field_order = ['network', 'name']

    name = argument.String()
    size = argument.Integer(default=25)
    network = argument.Resource(ip_allocations.Allocations)

    def clean_name(self, name):
        return self.network.name + '.' + name


class ApplyAction(Action):

    @property
    def description(self):
        yield 'Allocate a /{} within {}'.format(
            self.resource.size,
            self.resource.network.network,
        )

    def run(self):
        allocator = self.runner.get_service(self.resource.network, 'ip_allocator')
        allocation = allocator.allocate(self.resource.name, self.resource.size)
        self.runner.get_service(self.resource, 'set').execute(str(allocation))


class Apply(plan.Plan):

    resource = Allocation
    name = 'apply'

    def get_actions(self):
        try:
            self.runner.get_service(self.resource, 'get').execute()
        except KeyError:
            yield ApplyAction(self)


class Get(plan.Plan):

    resource = Allocation
    name = 'get'

    def execute(self):
        conf = self.runner.get_service(
            self.resource.network.config,
            'describe',
        )
        return conf.get(self.resource.name)


class Set(plan.Plan):

    resource = Allocation
    name = 'set'

    def from_string(self, value):
        return value

    def execute(self, value):
        conf = self.runner.get_service(
            self.resource.network.config,
            'describe',
        )
        return conf.set(self.resource.name, value)


class Describe(variable.Describe):

    resource = Allocation


argument.IPNetwork.register_adapter(Allocation, variable.VariableAsString)
