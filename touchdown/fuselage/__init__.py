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

import binascii
import os
import time

from touchdown.core import action, argument, errors, resource, plan, workspace

try:
    import fuselage
    from fuselage import bundle, builder, error
except ImportError:
    fuselage = None

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


class Bundle(resource.Resource):

    resource_name = "fuselage_bundle"

    ssh_connection = argument.Resource(Connection)
    resources = argument.List()

    root = argument.Resource(workspace.Workspace)


class Deployment(action.Action):

    @property
    def description(self):
        yield "Apply fuselage configruation to {}".format(self.resource.ssh_connection)

    def _run(self, transport, command):
        channel = transport.open_session()
        try:
            channel.exec_command(command)

            # We don't want a stdin
            channel.makefile('wb', -1).close()

            # FIXME: It would be better to block with select
            exit_status_ready = channel.exit_status_ready()
            while not exit_status_ready:
                while channel.recv_ready():
                    print channel.recv(1024)
                while channel.recv_stderr_ready():
                    print channel.recv_stderr(1024)
                time.sleep(1)
                exit_status_ready = channel.exit_status_ready()

            while channel.recv_ready():
                print channel.recv(1024)
            while channel.recv_stderr_ready():
                print channel.recv_stderr(1024)

            exit_code = channel.recv_exit_status()
            if exit_code != 0:
                raise errors.Error("Bundle deployment failed with exit code: {}".format(exit_code))
        finally:
            channel.close()

    def run(self):
        random_string = binascii.hexlify(os.urandom(4)).decode('ascii')
        path = 'fuselage_%s' % (random_string)

        b = bundle.ResourceBundle()
        b.extend(iter(self.resource.resources))
        bu = builder.build(b)

        client = self.get_plan(self.resource.ssh_connection).get_client()

        sftp = client.open_sftp()

        try:
            sftp.putfo(bu, path)
            sftp.chmod(path, 0o755)
            try:
                transport = client.get_transport()
                self._run(transport, "sudo " + path)
            finally:
                sftp.remove(path)
                pass
        finally:
            sftp.close()


class Apply(plan.Plan):

    name = "apply"
    resource = Bundle

    def get_actions(self):
        if not fuselage:
            raise errors.Error("You need the fuselage package to use the fuselage_bundle resource")

        yield Deployment(self)
