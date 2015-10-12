scp
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

Then you could scp files to and from it with::

    touchdown scp foo.txt worker:

And in reverse:

    touchdown scp worker:foo.txt /tmp/


You can use the following arguments:

.. program:: touchdown scp BOX

.. argument:: BOX

    The target you want to scp to/from.
