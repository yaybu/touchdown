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

import threading

from touchdown.core import argument, plan, resource

from . import IniFile


class Network(resource.Resource):

    resource_name = "ip_network"

    name = argument.String()
    network = argument.IPNetwork()
    config = argument.Resource(IniFile)


class NetworkApply(plan.Plan):

    """
    Given an ipaddress.ip_network, manage allocating it into smaller allocations
    """

    resource = Network
    name = "ip_allocator"

    def __init__(self, *args, **kwargs):
        super(NetworkApply, self).__init__(*args, **kwargs)
        self.allocations = {}
        self.free = {int(self.resource.network.prefixlen): [self.resource.network]}
        self.allocation_lock = threading.Lock()

    def allocate(self, name, prefixlen):
        if prefixlen < int(self.resource.network.prefixlen):
            raise ValueError("Cannot fit /{} inside /{}".format(prefixlen, self.resource.network.prefixlen))

        with self.allocation_lock:
            for i in range(prefixlen, int(self.resource.network.prefixlen) - 1, -1):
                if self.free.get(i, None):
                    selected = self.free[i].pop()
                    break
            else:
                raise ValueError(
                    "There is not enough space left to allocate a /{}".format(
                        prefixlen
                    )
                )

            while int(selected.prefixlen) < prefixlen:
                selected, leftover = selected.subnet(selected.prefixlen + 1)
                self.free[int(leftover.prefixlen)] = [leftover]

            self.allocations[name] = selected

        return selected
