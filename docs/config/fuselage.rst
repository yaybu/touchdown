Fuselage
========

You can use `Fuselage`_ to deploy configuration changes to servers created and
managed by Touchdown. Fuselage provides a pythonic API for building bundles of
configuration which can be deployed idempotently on any system with a python
interpreter.

.. _Fuselage: https://github.com/yaybu/fuselage


.. class:: Bundle

    You can create a bundle from the workspace::

        bundle = workspace.add_fuselage_bundle(
            target={
                "hostname": "localhost",
                "username": "user",
            }
        )

        bundle.add_file(
            name="/etc/apt/sources.list",
            contents="...",
        )


    .. attribute:: target

        The target of the deployment. A fuselage "bundle" will be built, copied
        to this target and executed.

        You can create a bundle from the workspace::

            bundle = workspace.add_fuselage_bundle(
                target={
                    "hostname": "localhost",
                    "username": "user",
                }
            )

        This will SSH to ``localhost`` as user ``user`` to execute the bundle.
        You can chain connections (a technique called jump-off hosts) to
        traverse bastions::

            bundle = workspace.add_fuselage_bundle(
                target={
                    "hostname": "host1",
                    "username": "user",
                    "proxy": {
                        "hostname": "host2",
                        "username": "fred",
                    }
                },
            )

        When used like this a connection will be made to host2. From there a
        second connection will be made from host2 to host1. This will be
        tunnelled inside the first connection using the ``direct-tcpip`` feature
        of SSH.

        Instead of passing a ``hostname`` you can pass ``instance``. This lets
        you connect to resources defined elsewhere in your configuration. This
        even works on :class:`~touchdown.aws.ec2.AutoScalingGroup` instances!::

            application_servers = aws.add_auto_scaling_group(
                name='my-application-servers',
            )

            bundle = workspace.add_fuselage_bundle(
                target={
                    "instance": application_servers,
                    "username": "user",
                },
            )

        You can also target your local machine directly. This won't use SSH.
        It's a dedicated transport that runs locally::

            bundle = workspace.add_fuselage_bundle(
                target=workspace.add_local(),
            )
