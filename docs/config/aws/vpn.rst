============
Hardware VPN
============

.. module:: touchdown.aws.vpc
   :synopsis: Virtual private network resources.


Amazon provide a hardware VPN facility for connecting your VPC to your corporate
datacenter over industry standard ipsec encryption. This is a dial-in service.
You connect to it, it does not connect to you.


VPN Connections
===============

.. currentmodule:: touchdown.aws.vpc

.. class:: VpnConnection

    You can create a VPN Connection in any VPC::

        vpn = vpn.add_vpn_connection(
            name='my-vpn-connection',
        )

    By default you can only create 10 VPN connections within an Amazon account.

    .. attribute:: name

        The name of the vpn connection. This field is required.

    .. attribute:: customer_gateway

        A :class:`CustomerGateway`. This field is required.

    .. attribute:: vpn_gateway

        A :class:`VpnGateway`. This field is required.

    .. attribute:: type

        The type of ``VpnConnection`` to create. The default is ``ipsec.1``.
        This is also the only currently supported value.

    .. attribute:: static_routes_only

        Set to True to only consider the routes defined in ``static_routes``.

    .. attribute:: static_routes

        A list of ip ranges in CIDR form.

    .. attribute:: tags

        A dictionary of tags to associate with this VPC. A common use of tags
        is to group components by environment (e.g. "dev1", "staging", etc) or
        to map components to cost centres for billing purposes.


Customer Gateway
----------------

.. currentmodule:: touchdown.aws.vpc

.. class:: CustomerGateway

    A CustomerGateway represents the non-Amazon end of a VpnConnection.

    You can create an customer gateway in any VPC::

        customer_gateway = vpc.add_customer_gateway(
            name='my-customer-gateway',
        )

    .. attribute:: name

        The name of the customer gateway. This field is required.

    .. attribute:: type

        The type of ``CustomerGateway`` to create. The default is ``ipsec.1``.
        This is also the only currently supported value.

    .. attribute:: public_ip

        The internet-routable IP address for the customer gateway's outside interface.

    .. attribute:: bgp_asn

        For devices that support BGP, the gateway's BGP ASN.

    .. attribute:: tags

        A dictionary of tags to associate with this VPC. A common use of tags
        is to group components by environment (e.g. "dev1", "staging", etc) or
        to map components to cost centres for billing purposes.


VPN Gateway
-----------

.. currentmodule:: touchdown.aws.vpc

.. class:: VpnGateway

    A VpnGateway represents the Amazon end of a VpnConnection.

    You can create an vpn gateway in any VPC::

        vpn_gateway = vpc.add_vpn_gateway(
            name='my-vpn-gateway',
        )

    .. attribute:: name

        The name of the vpn gateway. This field is required.

    .. attribute:: type

        The type of ``CustomerGateway`` to create. The default is ``ipsec.1``.
        This is also the only currently supported value.

    .. attribute:: availability_zone

        The availability zone to place the Vpn Gateway in.

    .. attribute:: tags

        A dictionary of tags to associate with this VPC. A common use of tags
        is to group components by environment (e.g. "dev1", "staging", etc) or
        to map components to cost centres for billing purposes.
