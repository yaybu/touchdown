Script
======

The provisioner can deploy a script to a target and execute it. This is great
for simple deployments.

.. class:: Script

    You can provision with a script from the workspace::

        script = workspace.add_script(
            script=(
                "#! /bin/bash\n"
                "echo 'hello'\n"
            ),
            target={
                "hostname": "localhost",
                "username": "user",
            }
        )

    .. attribute:: script

        A script to copy to the host and run. This could be any thing the
        target knows how to execute. For example::

            workspace.add_script(
                script=(
                    "#! /usr/bin/env python\n"
                    "print('hello from python')\n"
                ),
            )

    .. attribute:: target

        The target of the deployment. For example::

            script = workspace.add_script(
                target={
                    "hostname": "localhost",
                    "username": "user",
                }
            )

        See :class:`~touchdown.provisioner.Provisioner` for more examples.
