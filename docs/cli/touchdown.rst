=========
touchdown
=========

Installing touchdown into a virtualenv creates a ``touchdown`` command. It will
load a configuration from a ``Touchdownfile`` in the current directory.

The ``Touchdownfile`` is a python source code file. A workspace object is
predefined so you can just start defining resources::

    # My first Touchdownfile

    aws = workspace.add_aws(region='eu-west-1')
    vpc = aws.add_vpc(name='my-first-vpc', cidr_block="10.10.10.10/24")
    vpc.add_subnet(name='myfirst-subnet', cidr_block="10.10.10.10/25")


It takes the following arguments:

.. program:: touchdown

.. option:: --parallel

    Deploy this configuration in parallel. Uses the dependency information
    inferred from your configuration to do this safely. This is useful
    on AWS, where it allows Touchdown to create ElastiCache instances and
    RDS instances (which are slow to provisoion) at the same time.

    This will become the default in a future release.

.. option:: --serial

    Force Touchdown to deploy a configuration in serial.

    Unlike parallel mode, serial mode is deterministic.

    This is the default.

.. option:: --debug

    Turns on extra debug logging. This is quite verbose. For AWS configurations
    this will show you the API calls that are made.


There are a bunch of commands you can run against your Touchdown config:

.. toctree::

   apply
   destroy
   dot
