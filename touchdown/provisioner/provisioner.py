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

from touchdown.core import (
    action,
    argument,
    plan,
    resource,
    serializers,
    workspace,
)

from .step import Step


class Target(resource.Resource):
    resource_name = 'target'


class Provisioner(resource.Resource):

    resource_name = 'provisioner'

    name = argument.String()
    target = argument.Resource(Target)
    steps = argument.ResourceList(Step)

    root = argument.Resource(workspace.Workspace)


class RunScript(action.Action):

    @property
    def description(self):
        yield 'Applying {} to {}'.format(self.resource, self.resource.target)

    def run(self):
        client = self.get_plan(self.resource.target).get_client()
        for step in self.resource.steps:
            kwargs = serializers.Resource().render(self.runner, step)

            try:
                client.run_script(kwargs['script'])
            except Exception as e:
                self.plan.object['Result'] = 'Error'
                self.plan.object['ErrorMessage'] = str(e)
                raise

        self.plan.object['Result'] = 'Success'


class Describe(plan.Plan):

    name = 'describe'
    resource = Provisioner

    def describe_object(self):
        return {'Result': 'Pending'}

    def get_actions(self):
        self.object = self.describe_object()
        return []


class Apply(plan.Plan):

    name = 'apply'
    resource = Provisioner

    def get_actions(self):
        client = self.runner.get_plan(self.resource.target).get_client()
        for step in self.resource.steps:
            if self.runner.get_service(step, 'needs-running').needs_running(client):
                self.object = {'Result': 'Pending'}
                yield RunScript(self)
                break
        else:
            self.object = {'Result': 'Success'}


class Destroy(plan.Plan):

    name = 'destroy'
    resource = Provisioner

    def get_actions(self):
        # Provisioners explicitly do not participate in destruction
        return []
