# Copyright 2016 Isotoma Limited
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

import collections
import threading

import netaddr

from touchdown.core import argument, plan, resource, serializers

from . import IniFile


class Allocations(resource.Resource):

    resource_name = 'ip_allocations'

    name = argument.String()
    network = argument.IPNetwork()
    config = argument.Resource(IniFile)


class Describe(plan.Plan):

    resource = Allocations
    name = 'describe'

    def network(self):
        return serializers.maybe(self.resource.network).render(
            self.runner,
            self.resource,
        )

    def get_actions(self):
        conf = self.runner.get_service(self.resource.config, 'describe')
        self.object = {}
        for key, value in conf.walk(self.resource.name):
            self.object[key] = value
        self.runner.get_service(self.resource, 'ip_allocator').load(self.network(), self.object)
        return []


class IpAllocator(plan.Plan):

    '''
    Given an ipaddress.ip_network, manage allocating it into smaller allocations
    '''

    resource = Allocations
    name = 'ip_allocator'

    def __init__(self, *args, **kwargs):
        super(IpAllocator, self).__init__(*args, **kwargs)
        self.allocation_lock = threading.Lock()

    def load(self, network, state):
        '''
        Given a list of allocations that have already been applied, ensure that
        `self.allocations` and `self.free` is correct.
        '''
        network_set = netaddr.IPSet([network])
        state = {k: v for (k, v) in state.items() if netaddr.IPNetwork(v) in network}
        state_set = netaddr.IPSet(state.values())

        with self.allocation_lock:
            self.allocations = state
            self.free = collections.defaultdict(list)
            for network in (network_set - state_set).iter_cidrs():
                self.free[network.prefixlen].append(network)

    def allocate(self, name, prefixlen):
        network = self.runner.get_service(self.resource, 'describe').network()

        if prefixlen < int(network.prefixlen):
            raise ValueError('Cannot fit /{} inside /{}'.format(prefixlen, network.prefixlen))

        with self.allocation_lock:
            for i in range(prefixlen, int(network.prefixlen) - 1, -1):
                if self.free.get(i, None):
                    selected = self.free[i].pop()
                    break
            else:
                raise ValueError(
                    'There is not enough space left to allocate a /{}'.format(
                        prefixlen
                    )
                )

            while int(selected.prefixlen) < prefixlen:
                selected, leftover = selected.subnet(selected.prefixlen + 1)
                self.free[int(leftover.prefixlen)] = [leftover]

            self.allocations[name] = selected

        return selected
