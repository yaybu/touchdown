Elastic Compute Cloud
=====================

.. module:: touchdown.aws.ec2
   :synopsis: Elastic Compute Cloud resources.


Auto Scaling Group
------------------

.. class:: AutoScalingGroup

    .. attribute:: name

        A name for this AutoScalingGroup. This field is required. It must be
        unique within an AWS account

    .. attribute:: subnets

        A list of :class:`~touchdown.aws.vpc.subnet.Subnet` resources

    .. attribute:: launch_configuration

        A :class:`~touchdown.aws.ec2.LaunchConfiguration`.

    .. attribute:: max_size

        The maximum number of EC2 instances that can be started by this
        AutoScalingGroup.

    .. attribute:: min_size

        The minimum number of EC2 instances that must be running

    .. attribute:: desired_capacity

        The number of EC2 instances that should be running. Must be between
        min_size and max_size.

    .. attribute:: default_cooldown

        The amount of time (in seconds) between scaling activities.

    .. attribute:: health_check_type

        The kind of health check to use to detect unhealthy instances. By
        default if you are using ELB with the ASG it will use the same health
        checks as ELB.

    .. attribute:: load_balancers

        A list of :class:`~touchdown.aws.elb.LoadBalancer` resources. As
        instances are created by the auto scaling group they are added to these
        load balancers.


Key Pair
--------

.. class:: KeyPair

    In order to securely use SSH with an EC2 instance (whether created directly
    or via a AutoScalingGroup) you must first upload the key to the EC2 key
    pairs database. The KeyPair resource imports and keeps up to date an ssh
    public key.

    It can be used with any AWS account resource::

        aws.add_keypair(
            name="my-keypair",
            public_key=open(os.expanduser('~/.ssh/id_rsa.pub')),
        )

    .. attribute:: name

        The name of the key. This field is required.

    .. attribute:: public_key

        The public key material, in PEM form. Must be supplied in order to
        upload a key pair.


Launch Configuration
--------------------

.. class:: LaunchConfiguration

    .. attribute:: name

        A name for this LaunchConfiguration. This field is required. It must be
        unique within an AWS account

    .. attribute:: image
    .. attribute:: key_pair

        A :class:`~touchdown.aws.ec2.KeyPair`. This is the public key that gets
        injected to new ec2 instances created by this launch configuration.

    .. attribute:: security_groups

        A list of :class:`~touchdown.aws.vpc.SecurityGroup`.

    .. attribute:: user_data
    .. attribute:: instance_type
    .. attribute:: kernel
    .. attribute:: ramdisk
    .. attribute:: block_devices

        This is not supported yet.

    .. attribute:: instance_monitoring
    .. attribute:: spot_prince
    .. attribute:: instance_profile

        A :class:`~touchdown.aws.iam.InstanceProfile`. Use this to grant
        started instances a pair of ephemeral credentials for using other AWS
        services, such as S3.

    .. attribute:: ebs_optimized
    .. attribute:: associate_public_ip_address
    .. attribute:: placement_tenancy
