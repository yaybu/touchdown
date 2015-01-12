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
from touchdown.core.target import Target
from touchdown.core import argument

from .vpc import VPC
from touchdown.core import serializers
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy


class Rule(Resource):

    """
    Represents a rule in a security group.

    You shouldn't create ``Rule`` resources directly, they are created
    implicitly when defining a :py:class:`SecurityGroup`. For example::

        security_group = vpc.add_security_group(
            name='my-security-group',
            ingress=[
                {"port": 80, "network": "0.0.0.0/0"},
                {"port": 443, "network": "0.0.0.0/0"},
            ],
        )

    This will implicitly create 2 ``Rule`` resources.
    """

    resource_name = "rule"

    @property
    def dot_ignore(self):
        return self.security_group is None

    protocol = argument.String(default='tcp', choices=['tcp', 'udp', 'icmp'], field="IpProtocol")
    """ The network protocol to allow. By default this is ``tcp``. It can also
    be set to ``udp`` or ``icmp``. """

    port = argument.Integer(min=-1, max=32768)
    """ A port to allow access to. """

    from_port = argument.Integer(default=lambda r: r.port, min=-1, max=32768, field="FromPort")
    """ Instead of specifying ``port``, you can specify a range of ports
    starting at ``from_port`` """

    to_port = argument.Integer(default=lambda r: r.port, min=-1, max=32768, field="ToPort")
    """ If specifying a ``from_port`` you also need to specify a
    ``to_port``. """

    security_group = argument.Resource(
        "touchdown.aws.vpc.security_group.SecurityGroup",
        field="UserIdGroupPairs",
        serializer=serializers.ListOfOne(serializers.Dict(
            UserId=serializers.Property("OwnerId"),
            GroupId=serializers.Identifier(),
        )),
    )
    """ A :py:class:`SecurityGroup`. This other security group will be allowed
    access to members of the security group on the port/protocol specified. """

    network = argument.IPNetwork(
        field="IpRanges",
        serializer=serializers.ListOfOne(serializers.Dict(
            CidrIp=serializers.String(),
        )),
    )
    """ A network range specified in CIDR form. For example, you could specify
    ``0.0.0.0/0`` to allow the entire internet to access the specified
    port/protocol. """

    def matches(self, runner, rule):
        sg = None
        if self.security_group:
            sg = runner.get_target(self.security_group)
            # If the SecurityGroup doesn't exist yet then this rule can't exist
            # yet - so we can bail early!
            if not sg.resource_id:
                return False

        if self.protocol != rule['IpProtocol']:
            return False
        if self.from_port != rule.get('FromPort', None):
            return False
        if self.to_port != rule.get('ToPort', None):
            return False

        if sg and sg.object:
            for group in rule.get('UserIdGroupPairs', []):
                if group['GroupId'] == sg.resource_id and group['UserId'] == sg.object['OwnerId']:
                    return True

        if self.network:
            for network in rule.get('IpRanges', []):
                if network['CidrIp'] == str(self.network):
                    return True

        return False

    def __str__(self):
        name = super(Rule, self).__str__()
        if self.from_port == self.to_port:
            ports = "port {}".format(self.from_port)
        else:
            ports = "ports {} to {}".format(self.from_port, self.to_port)
        return "{}: {} {} from {}".format(name, self.protocol, ports, self.network if self.network else self.security_group)


class SecurityGroup(Resource):

    """
    Resources can be placed in SecurityGroup resources. A SecurityGroup then
    applies a set of rules about what incoming and outgoing traffic is allowed.

    You can create a SecurityGroup in any VPC::

        security_group = vpc.add_security_group(
            name='my-security-group',
            ingress=[dict(
                protocol='tcp',
                from_port=22,
                to_port=22,
                network='0.0.0.0/0',
            )],
        )
    """

    resource_name = "security_group"

    name = argument.String(field="GroupName")
    """ The name of the security group. This field is required."""

    description = argument.String(field="Description")
    """ A short description of the SecurityGroup. This is shown in the AWS
    console UI. """

    """ A list of rules for what IP's or components are allowed to access
    members of the security group."""
    ingress = argument.ResourceList(Rule)

    """ A list of rules for what IP's/components are accessible by members of
    this security group """
    egress = argument.ResourceList(
        Rule,
        default=lambda instance: [dict(protocol=-1, network=['0.0.0.0/0'])],
    )
    tags = argument.Dict()
    """ A dictionary of tags to associate with this VPC. A common use of tags
    is to group components by environment (e.g. "dev1", "staging", etc) or to
    map components to cost centres for billing purposes. """

    vpc = argument.Resource(VPC, field="VpcId")


class Describe(SimpleDescribe, Target):

    resource = SecurityGroup
    service_name = 'ec2'
    describe_action = "describe_security_groups"
    describe_list_key = "SecurityGroups"
    key = 'GroupId'

    def get_describe_filters(self):
        vpc = self.runner.get_target(self.resource.vpc)
        return {
            "Filters": [
                {'Name': 'group-name', 'Values': [self.resource.name]},
                {'Name': 'vpc-id', 'Values': [vpc.resource_id or '']}
            ],
        }


class Apply(SimpleApply, Describe):

    create_action = "create_security_group"

    def update_object(self):
        for local_rule in self.resource.ingress:
            for remote_rule in self.object.get("IpPermissions", []):
                if local_rule.matches(self.runner, remote_rule):
                    break
            else:
                yield self.generic_action(
                    "Authorize ingress {}".format(local_rule),
                    self.client.authorize_security_group_ingress,
                    GroupId=serializers.Identifier(),
                    IpPermissions=serializers.ListOfOne(serializers.Context(serializers.Const(local_rule), serializers.Resource())),
                )

        return

        for local_rule in self.resource.egress:
            for remote_rule in self.object.get("IpPermissionsEgress", []):
                if local_rule.matches(self.runner, remote_rule):
                    break
            else:
                yield self.generic_action(
                    "Authorize egress {}".format(local_rule),
                    self.client.authorize_security_group_egress,
                    GroupId=serializers.Identifier(),
                    IpPermissions=serializers.ListOfOne(serializers.Context(serializers.Const(local_rule), serializers.Resource())),
                )


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_security_group"
