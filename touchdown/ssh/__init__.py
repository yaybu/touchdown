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

import StringIO

from touchdown.core import adapters, argument, errors, resource, plan, serializers, workspace

try:
    import paramiko
except ImportError:
    paramiko = None


class Instance(adapters.Adapter):
    pass


def _get_private_key(runner, object):
    if not object:
        return None
    for cls in (paramiko.RSAKey, paramiko.ECDSAKey, paramiko.DSSKey):
        try:
            key = cls.from_private_key(StringIO.StringIO(object))
        except paramiko.SSHException:
            continue
        return key
    raise errors.Error("Invalid SSH private key")


class Connection(resource.Resource):

    resource_name = "ssh_connection"

    username = argument.String(default="root", field="username")
    password = argument.String(field="password")
    private_key = argument.String(
        field="pkey",
        serializer=serializers.Expression(_get_private_key),
    )
    hostname = argument.String(field="hostname")
    instance = argument.Resource(Instance, field="hostname", serializer=serializers.Resource())
    port = argument.Integer(field="port", default=22)

    proxy = argument.Resource("touchdown.ssh.Connection")

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

        kwargs = serializers.Resource().render(self.runner, self.resource)

        if self.resource.proxy:
            proxy = self.runner.get_plan(self.resource.proxy)
            transport = proxy.get_client().get_transport()
            kwargs['sock'] = transport.open_channel(
                'direct-tcpip',
                (kwargs['hostname'], kwargs['port']),
                ('', 0)
            )

        if not self.resource.password and not self.resource.private_key:
            kwargs['look_for_keys'] = True
            kwargs['allow_agent'] = True

        client.connect(**kwargs)

        self._client = client

        return client

    def get_actions(self):
        if not paramiko:
            raise errors.Error("Paramiko library is required to perform operations involving ssh")
        return []
