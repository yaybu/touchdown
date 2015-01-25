========
Fuselage
========

You can use `Fuselage`_ to deploy configuration changes to servers created and
managed by Touchdown. Fuselage provides a pythonic API for building bundles of
configuration which can be deployed idempotently on any system with a python
interpreter.

.. _Fuselage: https://github.com/yaybu/fuselage


..class:: Bundle

    You can create a bundle from the workspace::

        bundle = workspace.add_bundle(
            connection={
                "hostname": "localhost",
                "username": "user",
            }
            resources=[
                File(
                    name="/etc/apt/sources.list",
                    contents="...",
                )
            ]
        )

    When using bastion hosts you can chain connections::

        bundle = workspace.add_bundle(
            connection={
                "hostname": "host1",
                "username": "user",
                "proxy": {
                    "hostname": "host2",
                    "username": "fred",
                }
            },
            resources=[<snip>],
        )

    When used like this a connection will be made to host2. From there a second
    connection will be made from host2 to host1. This will be tunnelled inside
    the first connection using the ``direct-tcpip`` feature of SSH.

    Instead of passing a ``hostname`` you can pass ``instance``. This lets you
    connect to resources defined elsewhere in your configuration. This even
    works on :class:`~touchdown.aws.ec2.AutoScalingGroup` instances!::

        application_servers = aws.add_auto_scaling_group(
            name='my-application-servers',
        )

        bundle = workspace.add_bundle(
            connection={
                "instance": application_servers,
                "username": "user",
            },
            resources=[<snip>],
        )

    ..attribute:: connection

    ..attribute:: resources

        This is a list of fuselage resources to apply.
