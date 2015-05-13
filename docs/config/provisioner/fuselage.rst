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

        The target of the deployment. You can create a bundle from the workspace::

            bundle = workspace.add_fuselage_bundle(
                target={
                    "hostname": "localhost",
                    "username": "user",
                }
            )

        See :class:`~touchdown.provisioner.Provisioner` for more examples.


Resources
---------

Once you have a bundle you can add fuselage resources to it.

The following resources are available:

 * File
 * Line
 * Directory
 * Link
 * Execute
 * Checkout
 * Package
 * User
 * Group
 * Service

The fuselage documentation gives examples in the form::

    Line(
        name="/etc/selinux/config",
        match=r"^SELINUX",
        replace="SELINUX=disabled",
    )

You can do this in touchdown as follows::

    bundle.add_line(
        name="/etc/selinux/config",
        match=r"^SELINUX",
        replace="SELINUX=disabled",
    )

You might deploy minecraft to a server like this::

    bundle = workspace.add_fuselage_bundle(
        target={
            "hostname": "example.com",
            "username": "deploy",
        }
    )
    bundle.add_directory(
        name='/var/local/minecraft',
    )
    bundle.add_execute(
        command='wget https://s3.amazonaws.com/Minecraft.Download/versions/1.8/minecraft_server.1.8.jar',
        cwd="/var/local/minecraft",
        creates="/var/local/minecraft/minecraft_server.1.8.jar",
    )
    bundle.add_file(
        name='/var/local/minecraft/server.properties',
        contents=open('var_local_minecraft_server.properties').read(),
    )
    bundle.add_file(
        name="/etc/systemd/system/minecraft.service",
        contents=open("etc_systemd_system_minecraft.service"),
    )
    bundle.add_execute(
        command="systemctl daemon-reload",
        watches=['/etc/systemd/system/minecraft.service'],
    )
    bundle.add_execute(
        command="systemctl restart minecraft.service",
        watches=[
            "/var/local/minecraft/server.properties",
            "/etc/systemd/system/minecraft.service",
        ]
    )
