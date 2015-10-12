=========
touchdown
=========

Installing touchdown into a virtualenv creates a ``touchdown`` command. It will
load a configuration from a ``Touchdownfile`` in the current directory.

The ``Touchdownfile`` is a python source code file. A workspace object is
predefined so you can just start defining resources::

    # My first Touchdownfile

    aws = workspace.add_aws(region='eu-west-1')
    vpc = aws.add_vpc(name='my-first-vpc', cidr_block="10.10.10.0/24")
    vpc.add_subnet(name='myfirst-subnet', cidr_block="10.10.10.0/25")

You can apply this simple configuration with ``touchdown apply``::

    $ touchdown apply
    [100.00%] Building plan...
    Generated a plan to update infrastructure configuration:

    vpc 'my-first-vpc':
      * Creating vpc 'my-first-vpc'
      * Waiting for resource to exist
      * Display resource metadata
      * Set tags on resource my-first-vpc
          Name = my-first-vpc

    subnet 'myfirst-subnet':
      * Creating subnet 'myfirst-subnet'
      * Waiting for resource to exist
      * Display resource metadata
      * Set tags on resource myfirst-subnet
          Name = myfirst-subnet

    Do you want to continue? [Y/n] y
    [40.00%] [worker3] [vpc 'my-first-vpc'] Creating vpc 'my-first-vpc'
    [40.00%] [worker3] [vpc 'my-first-vpc'] Waiting for resource to exist
    [40.00%] [worker3] [vpc 'my-first-vpc'] Resource metadata:
    [40.00%] [worker3] [vpc 'my-first-vpc']     VpcId = vpc-72a31c17
    [40.00%] [worker3] [vpc 'my-first-vpc'] Set tags on resource my-first-vpc
    [40.00%] [worker3] [vpc 'my-first-vpc']     Name = my-first-vpc
    [60.00%] [worker5] [subnet 'myfirst-subnet'] Creating subnet 'myfirst-subnet'
    [60.00%] [worker5] [subnet 'myfirst-subnet'] Waiting for resource to exist
    [60.00%] [worker5] [subnet 'myfirst-subnet'] Resource metadata:
    [60.00%] [worker5] [subnet 'myfirst-subnet']     SubnetId = subnet-cf8f3a96
    [60.00%] [worker5] [subnet 'myfirst-subnet'] Set tags on resource myfirst-subnet
    [60.00%] [worker5] [subnet 'myfirst-subnet']     Name = myfirst-subnet

It's idempotent so you can run it again::

    $ touchdown apply
    [100.00%] Building plan...
    Planning stage found no changes were required.

And you can tear it down with ``touchdown destroy``::

    $ touchdown destroy
    [100.00%] Building plan...
    Generated a plan to update infrastructure configuration:

    subnet 'myfirst-subnet':
      * Destroy subnet 'myfirst-subnet'

    vpc 'my-first-vpc':
      * Destroy vpc 'my-first-vpc'

    Do you want to continue? [Y/n] y
    [20.00%] [worker1] [subnet 'myfirst-subnet'] Destroy subnet 'myfirst-subnet'
    [60.00%] [worker4] [vpc 'my-first-vpc'] Destroy vpc 'my-first-vpc'

It takes the following arguments:

.. program:: touchdown

.. option:: --serial

    Force Touchdown to deploy a configuration in serial. By default touchdown
    applies configuration in parallel using a dependency graph inferred from
    your configuration.

    Unlike parallel mode, serial mode is deterministic.

.. option:: --debug

    Turns on extra debug logging. This is quite verbose. For AWS configurations
    this will show you the API calls that are made.


There are a bunch of commands you can run against your Touchdown config:

.. toctree::

   apply
   cost
   destroy
   get_signin_url
   tail
   rollback
   scp
   snapshot
   ssh
   dot
