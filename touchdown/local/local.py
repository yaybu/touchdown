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

import subprocess

from touchdown.core import argument
from touchdown.core import action
from touchdown.core import errors
from touchdown.core import plan
from touchdown.core import resource
from touchdown.core import serializers
from touchdown.core import workspace


class Step(resource.Resource):

    dot_ignore = True


class Local(resource.Resource):

    resource_name = "local"

    steps = argument.List(argument.Resource(Step))
    root = argument.Resource(workspace.Workspace)


class ApplyStep(action.Action):

    def __init__(self, plan, step):
        super(ApplyStep, self).__init__(plan)
        self.step = step

    @property
    def description(self):
        yield "Applying step {}".format(self.step)

    def run(self):
        kwargs = serializers.Resource().render(self.runner, self.step)
        self.run_script(kwargs['script'], sudo=kwargs['sudo'])

    def run_script(self, script, sudo=True, stdout=None, stderr=None):
        command = [script]
        if sudo:
            command = ['sudo', script]
        proc = subprocess.Popen(
            command, stdout=stdout, stderr=stderr)
        output, error_output = proc.communicate()
        exit_code = proc.returncode
        if exit_code != 0:
            raise errors.CommandFailed(exit_code, output, error_output)


class Apply(plan.Plan):

    name = "apply"
    resource = Local

    def get_actions(self):
        for step in self.resource.steps:
            yield ApplyStep(self, step)
