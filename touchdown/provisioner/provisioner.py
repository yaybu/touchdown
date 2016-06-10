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


class Target(resource.Resource):
    resource_name = "target"


class Provisioner(resource.Resource):

    resource_name = "provisioner"

    target = argument.Resource(Target)
    root = argument.Resource(workspace.Workspace)


class RunScript(action.Action):

    @property
    def description(self):
        yield "Applying {} to {}".format(self.resource, self.resource.target)

    def run(self):
        kwargs = serializers.Resource().render(self.runner, self.resource)
        client = self.get_plan(self.resource.target).get_client()
        try:
            client.run_script(kwargs['script'])
            self.object["Result"] = "Success"
        except Exception as e:
            self.object["Result"] = "Error"
            self.object["ErrorMessage"] = str(e)
            raise


class Apply(plan.Plan):

    name = "apply"
    resource = Provisioner

    def get_actions(self):
        self.object = {"Result": "Pending"}
        if self.resource.target:
            yield RunScript(self)
