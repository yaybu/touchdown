Autoscaling
===========

.. module:: touchdown.aws.ec2
   :synopsis: Autoscaling your EC2 instances


Why should I use autoscaling?
-----------------------------

An :class:`~AutoScalingGroup` provides 2 kinds of automation:

 * Dynamic scaling in response to CloudWatch metrics. For example you can
   monitor the length of a queue and start extra workers if the queue is
   growing instead of declining.
 * Scheduled (time based) capacity changes

These are optional of course. You just manually manage the ``desired_capacity``
of a group to scale your application as you see fit.

Even if you are not using the scaling facilities of an autoscaling group there
is still a strong reason to use them. By creating a :class:`~AutoScalingGroup`
with ``min`` set to ``1`` and ``max`` set to ``1`` you ensure that AWS will
try to replace any instance that has failed. If the instance goes down it will
be replaced by a new one as defined by your launch configuration.


Setting up base autoscaling
---------------------------

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


Defining what to launch
-----------------------

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
    .. attribute:: spot_price
    .. attribute:: instance_profile

        A :class:`~touchdown.aws.iam.InstanceProfile`. Use this to grant
        started instances a pair of ephemeral credentials for using other AWS
        services, such as S3.

    .. attribute:: ebs_optimized
    .. attribute:: associate_public_ip_address
    .. attribute:: placement_tenancy


Dynamcing scaling based on CloudWatch
-------------------------------------

In this example we use a metric that will be populated by our application. It
contains the length of a task queue::

    queue1_length = aws.add_metric(
        name='queue1',
        namespace="Statsd/queue",
    )

We've also got an autoscaling group. This is a pool of workers that we want to
dynamically scale::

    worker = aws.add_auto_scaling_group(
        name='worker',
        min=1,
        max=4,
        launch_configuration=<snip>,
    )

We connect these together with an alarm and an autoscaling policy that will
scale the worker pool up::

    queue1_length.add_alarm(
        name='scaling-queue1-too-busy',
        statistic='Average',
        period=60,
        evaluation_periods=5,
        threshold=10,
        comparison_operator='GreaterThanOrEqualToThreshold',
        alarm_actions=[worker.add_policy(
            name='scale-up',
            adjustment_type='ChangeInCapacity',
            scaling_adjustment=1,
            cooldown=2 * 60,
        )],
    )

And then scale the pool back down::

    queue1_length.add_alarm(
        name='scaling-queue1-too-quiet',
        statistic='Average',
        period=60,
        evaluation_periods=5,
        threshold=0,
        comparison_operator='LessThanOrEqualToThreshold',
        alarm_actions=[worker.add_policy(
            name='scale-down',
            adjustment_type='ChangeInCapacity',
            scaling_adjustment=-1,
            cooldown=10 * 60,
        )],
    )


.. class:: AutoScalingPolicy

    .. attribute:: name

        A name for this policy. This field is required.

    .. attribute:: auto_scaling_group

        The :class:`~touchdown.aws.ec2.AutoScalingGroup` to apply this policy to.

    .. attribute:: adjustment_type

        The adjustment type. Valid values are:

        ``ChangeInCapacity``:
            Increases or decreases the existing capacity. For example, the current capacity of your Auto Scaling group is set to three instances, and you then create a scaling policy on your Auto Scaling group, specify the type as ``ChangeInCapacity``, and the adjustment as five. When the policy is executed, Auto Scaling adds five more instances to your Auto Scaling group. You then have eight running instances in your Auto Scaling group: current capacity (3) plus ChangeInCapacity (5) equals 8.
        ``ExactCapacity``:
            Changes the current capacity to the specified value. For example, if the current capacity is 5 instances and you create a scaling policy on your Auto Scaling group, specify the type as ExactCapacity and the adjustment as 3. When the policy is executed, your Auto Scaling group has three running instances.
        ``PercentChangeInCapacity``:
            Increases or decreases the capacity by a percentage. For example, if the current capacity is 10 instances and you create a scaling policy on your Auto Scaling group, specify the type as PercentChangeInCapacity, and the adjustment as 10. When the policy is executed, your Auto Scaling group has eleven running instances because 10 percent of 10 instances is 1 instance, and 10 instances plus 1 instance is 11 instances.

    .. attribute:: min_adjustment_step

        Used with ``adjustment_type`` with the value ``PercentChangeInCapacity``, the scaling policy changes the ``desired_capacity`` of the Auto Scaling group by at least the number of instances specified in the value.

    .. attribute:: scaling_adjustment

        The number by which to scale. ``adjustment_type`` determines the interpretation of this number (for example, as an absolute number or as a percentage of the existing group size). A positive increment adds to the current capacity and a negative value removes from the current capacity.

    .. attribute:: cooldown

        The amount of time, in seconds, after a scaling activity completes and before the next scaling activity can start.
