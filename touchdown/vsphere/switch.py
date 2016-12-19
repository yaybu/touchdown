# Copyright 2016 John Carr
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

from pyVmomi import vim

from touchdown.core import action, argument, plan, resource, utils

from .common import vmware_find_object
from .connection import Connection


class Switch(resource.Resource):

    resource_name = 'vswitch'

    name = argument.String(field='vswitchName')
    num_ports = argument.Integer(field='numPorts', default=1024)
    mtu = argument.Integer(field='mtu', default=1450)

    nic_name = argument.String(field='nicDevice')

    vsphere_endpoint = argument.Resource(Connection)


class CreateVirtualSwitch(action.Action):

    @property
    def description(self):
        yield 'Create virtual switch {!r}'.format(self.resource.name)

    def run(self):
        vss_spec = vim.host.VirtualSwitch.Specification()
        vss_spec.numPorts = self.resource.num_ports
        vss_spec.mtu = self.resource.mtu
        vss_spec.bridge = vim.host.VirtualSwitch.BondBridge(
            nicDevice=[self.resource.nic_name],
        )

        conn = self.runner.get_service(self.resource.switch.vsphere_endpoint, 'connection')
        host = vmware_find_object(conn.content, vim.HostSystem)
        host.configManager.networkSystem.AddVirtualSwitch(vswitchName=self.resource.name, spec=vss_spec)


class Describe(plan.Plan):

    name = 'describe'
    resource = Switch

    @utils.cached_property
    def remote_object(self):
        conn = self.runner.get_service(self.resource.vsphere_endpoint, 'connection')
        host = vmware_find_object(conn.content, vim.HostSystem)
        for switch in host.config.network.vswitch:
            if switch.name == self.resource.name:
                return switch


class Apply(plan.Plan):

    name = 'apply'
    resource = Switch

    signature = (
        plan.Present('name'),
    )

    def get_actions(self):
        if not self.runner.get_service(self.resource, 'describe').remote_object:
            yield CreateVirtualSwitch(self)
