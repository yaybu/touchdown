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
import select

from touchdown.core import errors
from touchdown.core.goals import Goal, register


def _eintr_retry(func, *args):
    while True:
        try:
            return func(*args)
        except (OSError, select.error) as e:
            if e.args[0] != errno.EINTR:
                raise


class PortForward(Goal):

    ''' Forward remote ports to local computer '''

    name = 'portfwd'
    mutator = False

    def get_plan_class(self, resource):
        plan_class = resource.meta.get_plan('portfwd')
        if not plan_class:
            plan_class = resource.meta.get_plan('describe')
        if not plan_class:
            plan_class = resource.meta.get_plan('null')
        return plan_class

    @classmethod
    def setup_argparse(cls, parser):
        parser.add_argument(
            dest='ports',
            metavar='PORT',
            nargs='+',
            type=str,
            help='Remote port to forward to local port (e.g. db=8093)',
        )

    def get_services(self, ports):
        services = self.collect_as_dict('portfwd')
        if not services:
            raise errors.Error('No port-forwardable resources are defined')

        for p in ports:
            if '=' not in p:
                raise errors.Error('Invalid port specification "{}"'.format(p))

            service, local_port = p.split('=', 1)

            if service not in services:
                raise errors.Error('Not a valid service: "{}". Must be one of: {}'.format(
                    service,
                    ', '.join(sorted(services.keys())),
                ))

            try:
                local_port = int(local_port)
            except ValueError:
                raise errors.Error('Not a valid port number: "{}"'.format(p))

            yield (services[service], local_port)

    def process_incoming_forever(self, servers):
        # This is broadly the same as a TCPServer.serve_forever, but we do it
        # for multiple ports/protocols at once
        try:
            while True:
                r, w, e = _eintr_retry(select.select, servers, [], [], 0.5)
                for server in r:
                    server._handle_request_noblock()
        except KeyboardInterrupt:
            self.ui.echo('Interupted. Exiting...')

    def execute(self, *ports):
        mappings = self.get_services(ports)
        servers = [s.start(lp) for s, lp in mappings]

        self.ui.echo('All requested port forwards started. Waiting for connections...')
        self.process_incoming_forever(servers)


register(PortForward)
