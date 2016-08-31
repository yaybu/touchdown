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

import errno
import os
import subprocess
import sys
import tempfile

from touchdown.core import argument, errors, plan, workspace

from .provisioner import Target


class Local(Target):

    resource_name = 'local'

    user = argument.String()
    state = argument.String(default=os.path.abspath('.fuselage'))

    root = argument.Resource(workspace.Workspace)


class Connection(object):

    def __init__(self, plan):
        self.plan = plan
        self.resource = plan.resource

    def get_path_contents(self, path):
        with open(path) as fp:
            return fp.read()

    def get_path_bytes(self, path):
        with open(path, 'rb') as fp:
            return fp.read()

    def run_script(self, script, args=None, sudo=False):
        fd, script_name = tempfile.mkstemp()
        try:
            with os.fdopen(fd, 'wb') as fh:
                fh.write(script.read())
            os.chmod(script_name, 0o755)

            command = [sys.executable, script_name]

            if self.resource.state:
                command.extend(['--state', os.path.abspath('.fuselage')])

            command.extend(args or [])

            proc = subprocess.Popen(command)
            output, error_output = proc.communicate()
            exit_code = proc.returncode
            if exit_code != 0:
                raise errors.CommandFailed(exit_code, output, error_output)
        finally:
            try:
                os.close(fd)
            except OSError as e:
                if e.errno != errno.EBADF:
                    raise
            if os.path.exists(script_name):
                os.unlink(script_name)


class LocalPlan(plan.Plan):

    name = 'describe'
    resource = Local

    def get_client(self):
        return Connection(self)

    def get_actions(self):
        return []
