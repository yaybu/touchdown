=======
Route53
=======

.. module:: touchdown.aws.route53
   :synopsis: Route53 resources.


HostedZone
==========

.. class:: HostedZone

    You can add a Route53 hosted zone from an AWS account resource::

        aws.add_hosted_zone(
            name="example.com",
            records=[
                {"type": "ALIAS", "load_balancer": my_load_balancer},
            ],
        )

    .. attribute:: name

        The name of the hosted zone.

    .. attribute:: comment

        A comment about the hosted zone that is shown in the AWS user
        interface.

    .. attribute:: records

        A list of :class:`Record` resources.

    .. attribute:: shared

        Set this to ``True`` in the zone is not exclusively managed by this
        touchdown configuration. Otherwise shared zones may be unexpectedly
        deleted.

    .. attribute:: vpc

        Set this to a :class:`Vpc` in order to create a private hosted zone.


DNS records
-----------

.. class:: Record

    .. attribute:: name

        For example, ``www``. This field is required.

    .. attribute:: type

        The type of DNS record. For example, ``A`` or ``CNAME``. This field is
        required.

    .. attribute:: set_identifier

        When using weighted recordsets this field differentiates between
        records for ``name``/``type`` pairs. It is only required in that case.

    .. attribute:: ttl

        How long the DNS record is cacheable for, in seconds.

    .. attribute:: values

        A list of values to return when a client resolves the given ``name``
        and ``type``.

    .. attribute:: load_balancer

        For ``ALIAS`` records you don't need to specify ``values``. Instead you
        can pass a :class:`LoadBalancer` resource. After the load balancer has
        been created and assigned a DNS name its ALIAS record will then be
        created.
