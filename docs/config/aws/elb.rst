Elastic Load Balancer
=====================

.. module:: touchdown.aws.elb
   :synopsis: Elastic Load Balancer resources.


Load Balancer
-------------

.. class:: LoadBalancer

    .. attribute:: name

        The name of your load balancer. This is required.

    .. attribute:: listeners

        A list of :class:`Listener` resources. Determines what ports the load
        balancer should listen on and where traffic for those ports should be
        directed. You can only set a single backend port. All your application
        servers should be listening on the same port, not on ephemeral ports.

    .. attribute:: subnets

        A list of :class:`~touchdown.aws.vpc.Subnet` resources. These are the
        subnets that the load balancer can create listeners in.

    .. attribute:: availability_zones

        A list of availability zones this load balancer can listen in. If you
        set ``subnets`` then this option is implied and can be left unset.

    .. attribute:: scheme

        By default this is ``private``. This means the database is created on
        private ip addresses and cannot be accessed directly from the internet.
        It can be set to internet-facing if you want it to have a public ip
        address.

    .. attribute:: security_groups

        A list of :class:`~touchdown.aws.vpc.SecurityGroup` resources. These
        determine which resources the LoadBalancer can access. For example,
        you could have a load balancer security group that only allowed access
        to your application instances, but not your database servers.

    .. attribute:: health_check

        A :class:`HealthCheck` instance that describes how the load balancer
        should determine the health of its members.

    .. attribute:: attributes

        A :class:`Attributes` instance. ELB attributes control the behavior of
        your instance.


Listeners
---------

.. class:: Listener

    .. attribute:: protocol

        The protocol to listen for. The choices are ``HTTP``, ``HTTPS``,
        ``TCP`` or ``TCPS``.

    .. attribute:: port

        A tcp/ip port to listen on.

    .. attribute:: instance_protocol

        The protocol that your backend expects.

    .. attribute:: instance_port

        The port that your backend is listening on.

    .. attribute:: ssl_certificate

        This is a :class:`~touchdown.aws.iam.ServiceCertificate`. This is
        required if your listener is over SSL.


Attributes
----------

.. class:: Attributes

    .. attribute:: idle_timeout

    .. attribute:: connection_draining

    .. attribute:: cross_zone_load_balacning

    .. attribute:: access_log

        An :class:`~touchdown.aws.s3.Bucket` for storing access logs in.


Health checks
-------------

.. class:: HealthCheck

    .. attribute:: interval

    .. attribute:: check

    .. attribute:: healthy_threshold

    .. attribute:: unhealthy_threshold

    .. attribute:: timeout
