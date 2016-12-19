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
from .switch import Switch


class PortGroup(resource.Resource):

    resource_name = 'port_group'

    name = argument.String(field='vswitchName')
    vlan_id = argument.Integer(field='vlanId', default=0)
    allow_promiscuous = argument.Boolean(field='allowPromiscuous', default=False)
    mac_changes = argument.Boolean(field='macChanges', default=False)
    forged_transmits = argument.Boolean(field='forgedTransmits', default=False)
    switch = argument.Resource(Switch, field='vswitchName')


class CreatPortGroup(action.Action):

    @property
    def description(self):
        yield 'Create port group {!r}'.format(self.resource.name)

    def run(self):
        port_group_spec = vim.host.PortGroup.Specification()
        port_group_spec.name = self.resource.name
        port_group_spec.vlanId = self.resource.vlan_id
        port_group_spec.vswitchName = self.resource.switch.name

        security_policy = vim.host.NetworkPolicy.SecurityPolicy()
        security_policy.allowPromiscuous = self.resource.allow_promiscuous
        security_policy.macChanges = self.resource.mac_changes
        security_policy.forgedTransmits = self.resource.forged_transmits
        port_group_spec.policy = vim.host.NetworkPolicy(security=security_policy)

        conn = self.runner.get_service(self.resource.switch.vsphere_endpoint, 'connection')
        host = vmware_find_object(conn.content, vim.HostSystem)
        host.configManager.networkSystem.AddPortGroup(portgrp=port_group_spec)


class Describe(plan.Plan):

    name = 'describe'
    resource = PortGroup

    @utils.cached_property
    def remote_object(self):
        conn = self.runner.get_service(self.resource.switch.vsphere_endpoint, 'connection')
        for datacenter in conn.content.rootFolder.childEntity:
            for network in datacenter.networkFolder.childEntity:
                if network.name == self.resource.name:
                    return network


class Apply(plan.Plan):

    name = 'apply'
    resource = PortGroup

    signature = (
        plan.Present('name'),
        plan.Present('switch'),
    )

    def get_actions(self):
        if not self.runner.get_service(self.resource, 'describe').remote_object:
            yield CreatPortGroup(self)
