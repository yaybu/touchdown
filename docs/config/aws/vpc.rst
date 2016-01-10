Virtual private clouds
======================

.. module:: touchdown.aws.vpc
   :synopsis: Virtual private cloud resources.


Virtual Private Clouds
----------------------

.. currentmodule:: touchdown.aws.vpc.vpc

.. class:: VPC

    A Virtual Private Cloud in an Amazon region.

    VPC's let you logically isolate components of your system. A properly
    defined VPC allows you to run most of your backend components on private IP
    addresses - shielding it from the public internet.

    You define the IP's available in your VPC with a `CIDR`_-form IP address.

    .. _CIDR: http://en.wikipedia.org/wiki/CIDR

    You can add a VPC to your workspace from any Amazon account resource::

        account = workspace.add_aws(
            access_key_id='....',
            secret_access_key='....',
            region='eu-west-1',
        )

        vpc = workspace.add_vpc(
            name='my-first-vpc',
            cidr_block='10.0.0.0/16',
        )

    .. attribute:: name

        The name of the VPC. This field is required.

    .. attribute:: cidr_block

        A network range in CIDR form. For example, 10.0.0.0/16. A VPC network
        should only use private IPs, and not public addresses. This field is
        required.

    .. attribute:: tenancy

        This controls whether or not to enforce use of single-tenant hardware
        for this VPC. If set to ``default`` then instances can be launched with
        any tenancy options. If set to ``dedicated`` then all instances started
        in this VPC will be launched as dedicated tenancy, regardless of the
        tenancy they requsest.

    .. attribute:: tags

        A dictionary of tags to associate with this VPC. A common use of tags
        is to group components by environment (e.g. "dev1", "staging", etc) or
        to map components to cost centres for billing purposes.

If you create a dedicated VPC for your application instead of using the default
VPC then you must create at least one :class:`Subnet` in it.


Subnets
-------

.. currentmodule:: touchdown.aws.vpc.subnet

.. class:: Subnet

    Subnets let you logically split application reponsibilities across
    different network zones with different routing rules and ACL's. You can
    also associate a subnet with an availability zone when building H/A
    solutions.

    You can add a subnet to any VPC::

        subnet = vpc.add_subnet(
            name='my-first-subnet',
            cidr_block='10.0.0.0/24',
        )

    .. attribute:: name

        The name of the subnet. This field is required.

    .. attribute:: cidr_block

        A network range specified in CIDR form. This field is required and must
        be a subset of the network range covered by the VPC. For example, it
        cannot be 192.168.0.0/24 if the parent VPC covers 10.0.0.0/24.

    .. attribute:: network_acl

        A :class:`~touchdown.aws.vpc.network_acl.NetworkACL` resource.

        This controls which IP address a subnet can connect out to an can
        receive connections from.

    .. attribute:: route_table

        A :class:`~touchdown.aws.vpc.route_table.RouteTable` resource.

        Where to route traffic external to the VPC. This controls whether to
        send traffic via an internet gateway, vpn gateway or via another
        instance that is applying NAT to traffic.

    .. attribute:: availability_zone

        The AWS availability zone this subnet is created in.

    .. attribute:: tags

        A dictionary of tags to associate with this VPC. A common use of tags
        is to group components by environment (e.g. "dev1", "staging", etc) or
        to map components to cost centres for billing purposes.

In order for a subnet to access the internet it will need a :class:`RouteTable`
attaching to it with an :class:`InternetGateway`.


Security Groups
---------------

.. currentmodule:: touchdown.aws.vpc.security_group

.. class:: SecurityGroup

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

    .. attribute:: name

        The name of the security group. This field is required.

    .. attribute:: description

        A short description of the SecurityGroup. This is shown in the AWS
        console UI.

    .. attribute:: ingress

        A list of :class:`Rule` resources describing what IP's or components
        are allowed to access members of the security group.

    .. attribute:: egress

        A list of :class: `Rule` resources describing what IP's or components
        can be access by members of this security group.

    .. attribute:: tags

        A dictionary of tags to associate with this VPC. A common use of tags
        is to group components by environment (e.g. "dev1", "staging", etc) or
        to map components to cost centres for billing purposes.

Defining rules
--------------

.. class:: Rule

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

    .. attribute:: protocol

        The network protocol to allow. It must be one of ``tcp``, ``udp`` or
        ``icmp``. It is ``tcp`` by default.

    .. attribute:: port

        The port to allow access to. You might want to specify a range instead.
        In that case you can set ``from_port`` and ``to_port`` instead.

    .. attribute:: security_group

        The :class: ``SecurityGroup`` that this rule is about. You cannot
        specify ``security_group`` and ``network`` on the same rule.

    .. attribute: network

        A network range specified in CIDR form. For example, you could specify
        ``0.0.0.0/0`` to allow the entire internet to access the specified
        port/protocol.


Network ACL's
-------------

.. currentmodule:: touchdown.aws.vpc.network_acl

.. class:: NetworkACL

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

    Network ACL's are updated by replacement. This means each time a change is
    detected an entirely new one will be created and subnets using the old one
    (that are managed by touchdown) will be pointed at the new one. This avoids
    having to re-number rules in an existing ACL and makes rolling back easier.

    .. attribute:: name

        The name of the network acl. This field is required.

    .. attribute: inbound

        List of :class:`Rule` resources that are applied to incoming traffic.

    .. attribute: outbound

        List of :class:`Rule` resources that are applied to outgoing traffic.

    .. attribute:: tags

        A dictionary of tags to associate with this VPC. A common use of tags
        is to group components by environment (e.g. "dev1", "staging", etc) or
        to map components to cost centres for billing purposes.

Defining rules
--------------

.. class:: Rule

    Represents a rule in a :class:`NetworkACL`.

    You shouldn't create ``Rule`` resources directly, they are created
    implicitly when defining a :class:`NetworkACL`. For example::

        network_acl = vpc.add_network_acl(
            name='my-network-acl',
            inbound=[
                {"port": 80, "network": "0.0.0.0/0"},
                {"port": 443, "network": "0.0.0.0/0"},
            ],
        )

    This will implicitly create 2 ``Rule`` resources.

    .. attribute: network

        A network range specified in CIDR form. For example, you could specify
        ``0.0.0.0/0`` to allow the entire internet to access the specified
        port/protocol. This field is required.

    .. attribute: protocol

        The network protocol to allow or deny. By default this is ``tcp``. It
        must be one of ``tcp``, `udp`` or ``icmp``.

    .. attribute: port

        A port to allow or deny access to/from. You must specify a ``port``.
        Alternatively you can specify a range of ports with by setting
        ``from_port`` and ``to_port``.

    .. attribute: action

        Whether to allow or deny matching traffic. The default value is ``ALLOW``.

There is always a default catch-all rule that denies any traffic you haven't
added a rule for.


Route Tables
------------

.. currentmodule:: touchdown.aws.vpc.route_table

.. class:: RouteTable

    A route table contains a list of routes. These are rules that are used to
    determine where to direct network traffic.

    A route table entry consists of a destination cidr and a component to use
    when to route that traffic. It is represented in touchdown by a
    :py:class:`Route` resource.

    You can create a route table in any vpc::

        vpc.add_route_table(
            name="internet_access",
            subnets=[subnet],
            routes=[dict(
                destination_cidr='0.0.0.0/0',
                internet_gateway=internet_gateway,
            )]
        )

    .. attribute:: name

        The name of the route table. This field is required.

    .. attribute:: routes

        A list of :py:class:`Route` resources to ensure exist in the route
        table.

    .. attribute:: propagating_vpn_gateways

        A list of :py:class:`VpnGateway` resources that should propagate their
        routes into this route table.

    .. attribute:: tags

        A dictionary of tags to associate with this VPC. A common use of tags
        is to group components by environment (e.g. "dev1", "staging", etc) or
        to map components to cost centres for billing purposes.

Defining routes
---------------

.. class:: Route

    Represents a route in a route table.

    You shouldn't create Route resources directly, they are created
    implicitly when defining a :py:class:`RouteTable`. For example::

        vpc.add_route_table(
            name="internet_access",
            routes=[
                {"destionation_cidr": "8.8.8.8/32", "internet_gateway": ig},
                {"destionation_cidr": "8.8.4.4/32", "internet_gateway": ig},
            ]
        )

    You should specify 2 attributes: ``destination_cidr`` and where to route
    that traffic.

    .. attribute:: destination_cidr

        A network range that this rule applies to in CIDR form. You can
        specificy a single IP address with ``/32``. For example,
        ``8.8.8.8/32``. To apply a default catch all rule you can specify
        ``0.0.0.0/0``. """

    .. attribute:: internet_gateway

        A :py:class:`InternetGateway` resource.

    .. attribute:: nat_gateway

        A :py:class:`NatGateway` resource.


Internet Gateway
----------------

.. currentmodule:: touchdown.aws.vpc.internet_gateway

.. class:: InternetGateway

    An internet gateway is the AWS component that allows you to physically
    connect your VPC to the internet. Without an internet gateawy connected to
    your VPC then traffic will not reach it, even if assigned public IP
    addresses.

    You can create an internet gateway in any VPC::

        internet_gateway = vpc.add_internet_gateway(
            name='my-internet-gateway',
        )

    .. attribute:: name

        The name of the gateway. This field is required.

    .. attribute:: tags

        A dictionary of tags to associate with this VPC. A common use of tags
        is to group components by environment (e.g. "dev1", "staging", etc) or
        to map components to cost centres for billing purposes.


NAT Gateway
-----------

.. currentmodule:: touchdown.aws.vpc.nat_gateway

.. class:: NatGateway

    An internet gateway is the AWS component that allows you connect a private VPC to the internet.

    You can create a NAT gateway in any subnet::

        nat_gateway = subnet.add_nat_gateway(
            elastic_ip=....,
        )

    .. attribute:: name

        You cannot assign a name to a NAT Gateway - it automatically inherits the name of the subnet it is placed in (i.e. its `Name` tag).

    .. attribute:: elastic_ip
