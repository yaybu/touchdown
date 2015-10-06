SSH
===

If you have defined an explicit ssh connection in your config::

    aws.add_auto_scaling_group(
        name=name,
        launch_configuration=...,
        <SNIP>,
    )

    workspace.add_ssh_connection(
        name="worker",
        instance="worker",
        username="ubuntu",
        private_key=open('foo.pem').read(),
    )

Then you could ssh into a random instead in the ``worker`` autoscaling group
with::

    touchdown ssh worker

You can use the following arguments:

.. program:: touchdown ssh BOX

.. argument:: BOX

    The target you want to SSH into.
