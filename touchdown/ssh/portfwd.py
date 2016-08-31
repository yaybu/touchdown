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

import select

from touchdown.core import argument, errors, plan, resource, serializers
from touchdown.ssh.connection import Connection

try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer


class PortForward(resource.Resource):

    resource_name = 'port_forward'

    name = argument.String()

    host = argument.String(field='host')
    port = argument.Integer(field='port')

    via = argument.Resource(Connection)


class ForwardServer (SocketServer.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


class Handler (SocketServer.BaseRequestHandler):

    def handle(self):
        try:
            chan = self.ssh_transport.open_channel(
                'direct-tcpip',
                (self.chain_host, self.chain_port),
                self.request.getpeername(),
            )
        except Exception as e:
            raise errors.Error(
                'Failed to connect to {}:{} ({})'.format(
                    self.chain_host,
                    self.chain_port,
                    repr(e),
                )
            )

        if chan is None:
            raise errors.Error(
                'Connect to {}:{} rejected by remote SSH server'.format(
                    self.chain_host,
                    self.chain_port,
                ),
            )

        self.plan.echo('Tunnel {} -> {} -> {} established'.format(
            self.request.getpeername(),
            chan.getpeername(),
            (self.chain_host, self.chain_port),
        ))

        while True:
            r, w, x = select.select([self.request, chan], [], [])
            if self.request in r:
                data = self.request.recv(1024)
                if len(data) == 0:
                    break
                chan.send(data)
            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0:
                    break
                self.request.send(data)

        peername = self.request.getpeername()
        chan.close()
        self.request.close()
        self.plan.echo('Tunnel closed from {}'.format(peername))


class ConnectionPlan(plan.Plan):

    name = 'portfwd'
    resource = PortForward

    def start(self, local_port):
        via = self.runner.get_service(self.resource.via, 'describe')
        transport = via.get_client().get_transport()

        params = serializers.Resource().render(self.runner, self.resource)

        class SubHandler (Handler):
            chain_host = params['host']
            chain_port = params['port']
            ssh_transport = transport
            plan = self

        server = ForwardServer(('', local_port), SubHandler)
        self.echo('Opening port *:{} -> {}:{}'.format(
            server.server_address[1],
            params['host'],
            params['port'],
        ))
        return server
