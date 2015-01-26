======================
Defining configuration
======================

When using touchdown as a standalone tool then your configuration should be
defined in the ``Touchdown`` file. A ``Touchdown`` file is a python file. The
``workspace`` variable will have been initialised for you so you can start
connecting the components in your infrastructure. For example, to create a new
VPC at Amazon with a subnet your ``Touchdownfile`` would contain::

    aws = workspace.add_aws(
        access_key_id='....',
        secret_access_key='....',
        region='eu-west-1',
    )

    vpc = aws.add_vpc(
        name='my-vpc,
        cidr_block='192.168.0.1/24',
    )

    vpc.add_subnet(name='subnet1', cidr_block='192.168.0.1/25')


.. toctree::

   aws/index
   fuselage
