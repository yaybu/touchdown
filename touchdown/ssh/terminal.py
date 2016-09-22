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

import os
import shutil
import tempfile
import time

from touchdown.core import plan, serializers

from .connection import Connection

try:
    from .agent import PosixAgentServer
except ImportError:
    PosixAgentServer = None


class SshMixin(object):

    def get_proxy_command(self):
        kwargs = serializers.Resource().render(self.runner, self.resource)
        cmd = [
            '/usr/bin/ssh',
            '-o', 'User="{username}"'.format(**kwargs),
            '-o', 'Port="{port}"'.format(**kwargs),
            '-W', '%h:%p',
            kwargs['hostname'],
        ]
        return ['-o', 'ProxyCommand={}'.format(' '.join(cmd))]

    def get_command_and_args(self):
        kwargs = serializers.Resource().render(self.runner, self.resource)
        cmd = [
            self.get_command(),
            '-o', 'User="{username}"'.format(**kwargs),
            '-o', 'Port="{port}"'.format(**kwargs),
            '-o', 'HostName="{hostname}"'.format(**kwargs),
        ]
        if self.resource.proxy:
            proxy = self.runner.get_plan(self.resource.proxy)
            cmd.extend(proxy.get_proxy_command())
        return cmd

    def run(self, args):
        cmd = self.get_command_and_args()
        cmd.extend(args)

        environ = os.environ.copy()

        if self.resource.private_key and PosixAgentServer:
            socket_dir = tempfile.mkdtemp(prefix='ssh-')
            socket_file = os.path.join(socket_dir, 'agent.{}'.format(os.getpid()))

            environ['SSH_AUTH_SOCK'] = socket_file
            del environ['SHELL']

            child_pid = os.fork()
            if child_pid:
                a = PosixAgentServer(socket_file)
                a.add(self.resource.private_key, 'touchdown.pem')
                try:
                    a.serve_while_pid(child_pid)
                finally:
                    shutil.rmtree(socket_dir)
                    return

            while not os.path.exists(socket_file):
                time.sleep(0.5)

        os.execvpe(cmd[0], cmd, environ)


class SshPlan(plan.Plan, SshMixin):

    name = 'ssh'
    resource = Connection

    def get_command(self):
        return '/usr/bin/ssh'

    def get_command_and_args(self):
        cmd = super(SshPlan, self).get_command_and_args()
        cmd.append('remote')
        return cmd

    def execute(self, args):
        self.run(args)


class ScpPlan(plan.Plan, SshMixin):

    name = 'scp'
    resource = Connection

    def get_command(self):
        return '/usr/bin/scp'

    def execute(self, source, destination):
        self.run([source, destination])
