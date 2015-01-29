Deploying Django at Amazon
==========================

We will deploy a simple Django application at Amazon with Touchdown. This
walkthrough will touch on:

 * Creating a :class:`~touchdown.aws.vpc.VPC` with multiple interconnected
   :class:`~touchdown.aws.vpc.Subnet`'s.

 * Creating and managing access to an S3 :class:`~touchdown.aws.s3.Bucket`.

 * Creating a :class:`~touchdown.aws.rds.Database` and passing its connection
   details to the Django instance.

 * Using an :class:`~touchdown.aws.ec2.AutoScalingGroup` to start an instance.

 * Using load balancing and CDN's to scale up your service.


To keep this first example east to digest we will miss out some steps:

 * We aren't going to worry about H/A best practices.


However we are going to build our application tier to be completely stateless.


Our application
---------------

For this tutorial we will deploy a simple blog application called radpress.

We have setup a project that has this installed.

FIXME: Publish demo project


Desiging your network
---------------------

We will create a subnet for each type of resource we plan to deploy. For our
demo this means there will be 3 subnets:

 * lb
 * app
 * db

The only tier that will have public facing IP's is the lb tier.

::

    vpc = aws.add_vpc('radpress')

    subnets = {}
    for subnet in ('lb', 'app', 'db'):
        subnets[subnet] = vpc.add_subnet(
            name=subnet,
            cidr_block='.....',
        )


Configuring S3
--------------

We'll create a bucket called ``radpress``::

    bucket = aws.add_bucket(name='radpress')

This will create a ``public-read``, which is fine for our blog. However our
EC2 instances need to be able to uploaded media to it. For this we'll use
an :class:`~touchdown.aws.iam.InstanceProfile` to grant a
:class:`~touchdown.aws.iam.Role` to the instance.

::

    instance_profile = aws.add_instance_profile(
        name="radpress-app",
        roles=[aws.add_role(
            name="radpress-app",
            assume_role_policy={
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": "ec2.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }],
            },
            policies={
                "app": {
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Resource": "arn:aws:s3:::radpress",
                        "Effect": "Allow",
                        "Action": [
                            "s3:ListBucketVersions",
                            "s3:ListBucket"
                        ]
                    }, {
                        "Resource": "arn:aws:s3:::radpress/*",
                        "Effect": "Allow",
                        "Action": [
                            "s3:GetObjectVersion",
                            "s3:DeleteObject",
                            "s3:DeleteObjectVersion",
                            "s3:GetObject",
                            "s3:PutObjectAcl",
                            "s3:PutObject"
                        ]
                    }]
                }
            },
        )],
    )

The ``assume_role_policy`` restricts who or what can assume a role. We restrict
it to our EC2 instances.

We then add permissions to inspect the bucket and to put/get/delete its
contents. With this in place, our ec2 instance will be able to request
temporary credentials from aws for accessing s3.


Adding a database
-----------------

Building your base image
------------------------

Deploying an instance
---------------------

We'll deploy the image we just made with an auto scaling group. We are going to
put a load balancer in front, which we'll set up first::

    aws.add_load_balancer(
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
        name="radpress-app",
        launch_configuration=aws.add_launch_configuration(
            name="radpress-app-{}".format(int(time.time())),
            image=ami,
            instance_type="t1.micro",
            user_data="",
            key_pair=keypair,
            security_groups=security_groups["app"],
            associate_public_ip_address=True,
            instance_profile=instance_profile,
        ),
        min_size=1,
        max_size=1,
        load_balancers=[lb],
        subnets=subnets["app"],
    )


Content delivery networks
-------------------------
