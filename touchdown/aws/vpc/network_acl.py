# Copyright 2014 Isotoma Limited
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

from touchdown.core.resource import Resource
from touchdown.core.plan import Plan
from touchdown.core import argument

from .vpc import VPC
from touchdown.core import serializers
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy


class Rule(Resource):

    """
    Represents a rule in a :py:class:`NetworkACL`.

    You shouldn't create ``Rule`` resources directly, they are created
    implicitly when defining a :py:class:`NetworkACL`. For example::

        network_acl = vpc.add_network_acl(
            name='my-network-acl',
            inbound=[
                {"port": 80, "network": "0.0.0.0/0"},
                {"port": 443, "network": "0.0.0.0/0"},
            ],
        )

    This will implicitly create 2 ``Rule`` resources.
    """

    resource_name = "rule"
    dot_ignore = True

    network = argument.IPNetwork(
        field="IpRanges",
        serializer=serializers.ListOfOne(serializers.Dict(
            CidrIp=serializers.String(),
        )),
    )
    """ A network range specified in CIDR form. For example, you could specify
    ``0.0.0.0/0`` to allow the entire internet to access the specified
    port/protocol. """

    protocol = argument.String(default='tcp', choices=['tcp', 'udp', 'icmp'], field="IpProtocol")
    """ The network protocol to allow or deny. By default this is ``tcp``. It can also
    be set to ``udp`` or ``icmp``. """

    port = argument.Integer(min=-1, max=32768)
    """ A port to allow access to. """

    from_port = argument.Integer(default=lambda r: r.port, min=-1, max=32768, field="FromPort")
    """ Instead of specifying ``port``, you can specify a range of ports
    starting at ``from_port`` """

    to_port = argument.Integer(default=lambda r: r.port, min=-1, max=32768, field="ToPort")
    """ If specifying a ``from_port`` you also need to specify a
    ``to_port``. """

    action = argument.String(default="ALLOW", choices=["ALLOW", "DENY"])
    """ Whether to allow or deny matching traffic. The default value is ``ALLOW``. """

    def __str__(self):
        name = super(Rule, self).__str__()
        if self.from_port == self.to_port:
            ports = "port {}".format(self.from_port)
        else:
            ports = "ports {} to {}".format(self.from_port, self.to_port)
        return "{}: {} {} from {}".format(name, self.protocol, ports, self.network)


class NetworkACL(Resource):

    """
    Network ACL's provide network filtering at subnet level, controlling both
    inbound and outbound traffic. They are:

     * Stateless. This means that return traffic is not automatically
       allowed. This can make them more difficult to set up.
     * Attached to the subnet. So you don't have to specify them when
       starting an instance.
     * Processed in the order specified. The first match is the rule that
       applies.
     * Supports ALLOW and DENY rules.

    Any traffic that doesn't match any rule is blocked.

    You can create a NetworkACL in any VPC::

        network_acl = vpc.add_network_acl(
            name='my-network-acl',
            inbound=[dict(
                protocol='tcp',
                port=22,
                network='0.0.0.0/0',
            )],
        )
    """

    resource_name = "network_acl"

    name = argument.String(field="GroupName")
    """ The name of the security group. This field is required."""

    inbound = argument.ResourceList(Rule)
    """ Rules for traffic entering the subnet. """

    outbound = argument.ResourceList(Rule)
    """ Rules for traffic leaving the subnet. """

    tags = argument.Dict()
    """ A dictionary of tags to associate with this VPC. A common use of tags
    is to group components by environment (e.g. "dev1", "staging", etc) or to
    map components to cost centres for billing purposes. """

    vpc = argument.Resource(VPC, field="VpcId")


class Describe(SimpleDescribe, Plan):

    resource = NetworkACL
    service_name = 'ec2'
    describe_action = "describe_network_acls"
    describe_list_key = "NetworkAcls"
    key = 'NetworkAclId'

    def get_describe_filters(self):
        vpc = self.runner.get_plan(self.resource.vpc)
        if not vpc.resource_id:
            return None

        return {
            "Filters": [
                {'Name': 'tag:Name', 'Values': [self.resource.name]},
                {'Name': 'vpc-id', 'Values': [vpc.resource_id]}
            ],
        }


class Apply(SimpleApply, Describe):

    create_action = "create_network_acl"

    def _get_local_rules(self):
        local_rules = {}
        for i, rule in enumerate(self.resource.inbound):
            rule = serializers.Resource().render(self.runner, rule)
            rule['RuleNumber'] = i
            local_rules[(False, i)] = rule

        for i, rule in enumerate(self.resource.outbound):
            rule = serializers.Resource().render(self.runner, rule)
            rule['RuleNumber'] = i
            local_rules[(True, i)] = rule
        return local_rules

    def _get_remote_rules(self):
        remote_rules = {}
        for rule in self.object.get("Entries", []):
            remote_rules[(rule['Egress'], rule['RuleNumber'])] = rule
        return remote_rules

    def update_object(self):
        for action in super(Apply, self).update_object():
            yield action

        local_rules = self._get_local_rules()
        remote_rules = self._get_remote_rules()

        for key, rule in local_rules.items():
            if key not in self.remote_rules or self.remote_rules[key] != rule:
                #FIXME: Rule stale or out of date
                print("UPSERT", rule)

        for rule in remote_rules.keys():
            if rule not in local_rules:
                #FIXME: Delete remote rule not present @ local
                print("DELETE", remote_rules[rule])


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_network_acl"
