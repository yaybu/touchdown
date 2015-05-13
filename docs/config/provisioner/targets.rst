Targets
=======

The provisioner can target multiple systems. It's primary mechanisms for
provisioning are:

 * Localhost direct access
 * SSH (including jump-off hosts)


.. class:: Provisioner

    You cannot directly add a provisioner to your workspace. You must add a specific type of provisioner to your workspace:

     * :class:`~touchdown.provisoner.Fuselage`
     * :class:`~touchdown.provisoner.Bash`

    However all provisioner types support the attributes below.

    .. attribute:: target

        The target of the deployment.

        You can target your local machine directly. This won't use SSH.
        It's a dedicated transport that runs locally::

            bundle = workspace.add_fuselage_bundle(
                target=workspace.add_local(),
            )

        You can provide SSH connection details::

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
        tunneled inside the first connection using the ``direct-tcpip`` feature
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
