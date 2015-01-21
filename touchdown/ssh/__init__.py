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

from touchdown.core import argument, errors, resource, plan, workspace

try:
    import paramiko
except ImportError:
    paramiko = None


class Connection(resource.Resource):

    resource_name = "ssh_connection"

    username = argument.String(default="root")
    password = argument.String()
    hostname = argument.String()
    port = argument.Integer(default=22)

    proxy = argument.Resource("touchdown.fuselage.Connection")

    root = argument.Resource(workspace.Workspace)


class ConnectionPlan(plan.Plan):

    name = "describe"
    resource = Connection
    _client = None

    def get_client(self):
        if self._client:
            return self._client

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        sock = None
        if self.resource.proxy:
            proxy = self.runner.get_plan(self.resource.proxy)
            transport = proxy.get_client().get_transport()
            sock = transport.open_channel(
                'direct-tcpip',
                (self.resource.hostname, int(self.resource.port)),
                ('', 0)
            )

        kwargs = dict(
            hostname=self.resource.hostname,
            port=self.resource.port,
            username=self.resource.username,
            sock=sock,
        )
        if self.resource.password:
            kwargs['password'] = self.resource.password

        client.connect(**kwargs)

        self._client = client

        return client

    def get_actions(self):
        if not paramiko:
            raise errors.Error("Paramiko library is required to perform operations involving ssh")
        return []
