=========
touchdown
=========

Installing touchdown into a virtualenv creates a ``touchdown`` command. It will
load a configuration from a ``Touchdownfile`` in the current directory.

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


.. toctree::

   apply
   destroy
   dot
