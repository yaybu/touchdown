Deploying Django at Amazon
==========================

We will deploy a simple Django application at Amazon with Touchdown. This
walkthrough will touch on:

 * Creating a :class:`~touchdown.aws.vpc.vpc.VPC` with multiple interconnected
   :class:`~touchdown.aws.vpc.subnet.Subnet`'s.

 * Creating a :class:`~touchdown.aws.rds.Database` and passing its connection
   details to the Django instance.

 * Using an :class:`~touchdown.aws.ec2.AutoScalingGroup` to start an instance.

 * Using a :class:`~touchdown.aws.elb.LoadBalancer` to scale up your service.


Our application
---------------

For this tutorial we will deploy a sentry server at AWS.


Desiging your network
---------------------

We will create a subnet for each type of resource we plan to deploy. For our
demo this means there will be 3 subnets:

 =======   =======           ========
 segment   network           ingress
 =======   =======           ========
 lb        192.168.0.0/24    0.0.0.0/0:80
                             0.0.0.0/0:443
 app       192.168.0.1/24    lb:80
 db        192.168.0.2/24    app:5432
 =======   =======           ========

The only tier that will have public facing IP's is the lb tier.

::

    vpc = aws.add_vpc('sentry')

    subnets = {
        'lb': vpc.add_subnet(
            name="lb",
            cidr_block='192.168.0.0/24',
        ),
        'app': vpc.add_subnet(
            name="app",
            cidr_block='192.168.0.1/24',
        ),
        'db': vpc.add_subnet(
            name="db",
            cidr_block='192.168.0.2/24',
        ),
    }

    security_groups = {
        'lb': vpc.add_security_group(
            name="lb",
            ingress=[
                {"port": 80, "network": "0.0.0.0/0"},
                {"port": 443, "network": "0.0.0.0/0"},
            ],
        ),
        'app': vpc.add_security_group(
            name="app",
            ingress=[
                {"port": 80, "security_group": subnets["lb"]},
            ],
        ),
        'db': vpc.add_security_group(
            name="db",
            ingress=[
                {"port": 5432, "security_group": subnets["app"]},
            ],
        ),
    }


Adding a database
-----------------

Rather than manually deploying postgres on an EC2 instance we'll use RDS to
provision a managed :class:`~touchdown.aws.rds.Database`::

    database = aws.add_database(
        name=sentry,
        allocated_storage=10,
        instance_class='db.t1.micro',
        engine="postgres",
        db_name="sentry",
        master_username="sentry",
        master_password="password",
        backup_retention_period=8,
        auto_minor_version_upgrade=True,
        publically_accessible=False,
        storage_type="gp2",
        security_groups=[security_groups['db']],
        subnet_group=aws.add_db_subnet_group(
            name="sentry",
            subnets=subnets['db'],
        )
    )


Building your base image
------------------------

We'll setup a fuselage bundle to describe what to install on the base ec2
image::

    provisioner = workspace.add_fuselage_bundle()

One unfortunate problem with Ubuntu 14.04 is that you can SSH into it before it
is ready. ``cloud-init`` is still configuring it, and so if you start deploying
straight away you will hit race conditions. So we'll wait for ``cloud-init`` to
finish::

    # Work around some horrid race condition where cloud-init hasn't finished running
    # https://bugs.launchpad.net/cloud-init/+bug/1258113
    provisioner.add_execute(
        command="python -c \"while not __import__('os').path.exists('/run/cloud-init/result.json'): __import__('time').sleep(1)\"",
    )

Then we'll install some standard python packages::

    provisioner.add_package(name="python-virtualenv")
    provisioner.add_package(name="python-dev")
    provisioner.add_package(name="libpq-dev")

We are going to deploy the app into a virtualenv at ``/app``. We'll do the
deployment as root, and at runtime the app will use the `sentry` user. We'll
create a ``/app/etc`` directory to keep settings in::

    provisioner.add_group(name="django")

    provisioner.add_user(
        name="django",
        group="django",
        home="/app",
        shell="/bin/false",
        system=True,
    )

    provisioner.add_directory(
        name='/app',
        owner='root',
        group='root',
    )

    provisioner.add_directory(
        name='/app/etc',
        owner='root',
        group='root',
    )

    provisioner.add_directory(
        name='/app/var',
        owner='root',
        group='root',
    )

    provisioner.add_execute(
        name="virtualenv",
        command="virtualenv /app",
        creates="/app/bin/pip",
        user="root",
    )

To actually provision this as an AMI we use the
:class:`~touchdown.aws.ec2.Image` resource::

    image = aws.add_image(
        name="sentry-demo",
        source_ami='ami-d74437a0',
        username="ubuntu",
        provisioner=provisioner,
    )


Deploying an instance
---------------------

We'll deploy the image we just made with an auto scaling group. We are going to
put a load balancer in front, which we'll set up first::

    lb = aws.add_load_balancer(
        name='balancer',
        listeners=[
            {"port": 80, "protocol": "http", "instance_port": 8080, "instance_protocol": "http"}
        ],
        subnets=subnets['delivery'],
        security_groups=[security_groups['delivery']],
        health_check={
            "interval": 30,
            "healthy_threshold": 3,
            "unhealthy_threshold": 5,
            "check": "HTTP:8080/__ping__",
            "timeout": 20,
        },
        attributes={
            "cross_zone_load_balancing": True,
            "connection_draining": 30,
        },
    )


Then we need a :class:`~touchdown.aws.ec2.LaunchConfiguration` that says what
any started instances should look like and the
:class:`~touchdown.aws.ec2.AutoScalingGroup` itself::

    app = aws.add_auto_scaling_group(
        name="sentry-app",
        launch_configuration=aws.add_launch_configuration(
            name="sentry-app",
            image=ami,
            instance_type="t1.micro",
            user_data="",
            key_pair=keypair,
            security_groups=security_groups["app"],
            associate_public_ip_address=False,
        ),
        min_size=1,
        max_size=1,
        load_balancers=[lb],
        subnets=subnets["app"],
    )
