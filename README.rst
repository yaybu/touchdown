=========
Touchdown
=========

.. image:: https://travis-ci.org/yaybu/touchdown.png?branch=master
   :target: https://travis-ci.org/#!/yaybu/touchdown

.. image:: https://coveralls.io/repos/yaybu/touchdown/badge.png?branch=master
    :target: https://coveralls.io/r/yaybu/touchdown

.. image:: https://pypip.in/version/touchdown/badge.png
    :target: https://pypi.python.org/pypi/touchdown/


Touchdown is a service orchestration framework for python.

You can find us in #yaybu on irc.oftc.net.


Examples
========

Here is an example ``Touchdownfile``::

    aws = workspace.aws(
        region='eu-west-1',
    )

    vpc = aws.virtual_private_cloud(name='example')
    vpc.add_internet_gateway(name="internet")

    example = vpc.subnet(
        name='example',
        cidr_block='192.168.0.1/24',
    )

    asg = aws.autoscaling_group(
        name='example',
        launch_configuration=aws.launch_configuration(
            name="example",
            ami='ami-62366',
            subnets=[example],
            user_data=json.dumps({
                "SECRET_KEY": "059849utiruoierutiou45",
            })
        ),
    )

You can then apply this configuration with::

    touchdown apply
