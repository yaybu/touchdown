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

from touchdown.core import adapters, argument, errors, plan, serializers, workspace
from .agent import AgentServer


class ConnectionPlan(plan.Plan):

    name = "ssh"
    resource = Connection

    def get_proxy_command(self):
        kwargs = serializers.Resource().render(self.runner, self.resource)
        cmd = 'ssh -A -l {username} -W %h:%p {hostname} {port}'.format(kwargs)
        return ['-o', 'ProxyCommand={}'.format(cmd)]

    @classmethod
    def setup_argparse(cls, parser):
        parser.add_argument(
            "box",
            metavar="BOX",
            type=str,
            help="The resource to ssh to",
        )

    def execute(self):
        cmd = ['ssh', '-A', '-l', self.resource.username]
        if self.resource.proxy:
            proxy = self.runner.get_plan(self.resource.proxy)
            cmd.extend(proxy.get_proxy_command())
        cmd.extend([self.resource.hostname, self.resource.port])
        print cmd

        socket_dir = tempfile.mkdtemp(prefix='ssh-')
        socket_file = os.path.join(socket_dir, 'agent.{}'.format(os.getpid()))

        child_pid = os.fork()
        if child_pid:
            a = AgentServer(socket_file)
            a.add(self.resource.private_key, "touchdown.pem")
            try:
                a.serve_while_pid(child_pid)
            finally:
                shutil.rmtree(socket_dir)
            return

        while not os.path.exists(socket_file):
            time.sleep(0.5)

        os.execvpe("/usr/bin/ssh", cmd, {"SSH_AUTH_SOCK": socket_file})
