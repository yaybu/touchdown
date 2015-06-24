Cloudwatch
==========

.. module:: touchdown.aws.cloudwatch
   :synopsis: CloudWatch resources.


EC2 is the main workhorse of an AWS solution. It allows you to (manually or
automatically) start virtual machines to run your application code.

.. note:: We recommend that your EC2 machines are stateless.


Metric
------

.. class:: Metric

    This is a value that is tracked in the AWS CloudWatch service.

    .. attribute:: name

        The name of the metric.

    .. attribute:: namespace



Alarm
-----

.. class:: Alarm

    .. attribute:: name

        Required. The name of the alarm. It must be unique within the account.

    .. attribute:: description

        A human readable description of the alarm. May be up to 255 characters.

    .. attribute:: actions_enabled

        If set to ``True`` then the actions defined will be executed when the alarm changes state.

    .. attribute:: ok_actions

        A list of resources to notify when the alarm enters the ``OK`` state. Must be one of the following types:

          * :class:`~touchdown.aws.sqs.Queue`
          * :class:`~touchdown.aws.ec2.Policy`

    .. attribute:: alarm_actions

        A list of resources to notify when the alarm enters the ``ALARM`` state. Must be one of the following types:

          * :class:`~touchdown.aws.sqs.Queue`
          * :class:`~touchdown.aws.ec2.Policy`

    .. attribute:: insufficient_data_actions

        A list of resources to notify when the alarm enters the ``INSUFFICIENT_DATA`` state. Must be one of the following types:

          * :class:`~touchdown.aws.sqs.Queue`
          * :class:`~touchdown.aws.ec2.Policy`

    .. attribute:: metric

        The metric this alarm is to respond to.

    .. attribute:: dimensions

        Up to 10 dimensions for the associated metric. Use this to restrict the
        metric to a particular ec2 instance id or load balancer id.

    .. attribute:: statistic

        The statistic to apply to the associated metric. Must be one of:

          * ``SampleCount``
          * ``Average``
          * ``Sum``
          * ``Minimum``
          * ``Maximum``

    .. attribute:: period

        The period in seconds over which the specified statistic is applied.

    .. attribute:: unit

        The unit for the alarm's associated metric. If specified, must be one of:

          * ``Seconds``
          * ``Microseconds``
          * ``Milliseconds``
          * ``Bytes``
          * ``Kilobytes``
          * ``Megabytes``
          * ``Gigabytes``
          * ``Terabytes``
          * ``Bits``
          * ``Kilobits``
          * ``Megabits``
          * ``Gigabits``
          * ``Terabits``
          * ``Percent``
          * ``Count``
          * ``Bytes/Second``
          * ``Kilobytes/Second``
          * ``Megabytes/Second``
          * ``Gigabytes/Second``
          * ``Terabytes/Second``
          * ``Bits/Second``
          * ``Kilobits/Second``
          * ``Megabits/Second``
          * ``Gigabits/Second``
          * ``Terabits/Second``
          * ``Count/Second``
          * ``None``

    .. attribute:: evaluation_periods

        The number of periods over which data is compared to the specified threshold.

    .. attribute:: threshold

        The value against which the specified statistic is compared.

    .. attribute:: comparison_operator

        The operation to use when comparing ``statistic`` and ``threshold``. For example, to dest when the statistic is less than threshold::

            aws.add_alarm(
                name='myalarm',
                statistic='Average',
                threshold=5,
                comparison_operator='LessThanThreshold',
            )

        Must be one of:

          * ``GreaterThanOrEqualToThreshold``
          * ``GreaterThanThreshold``
          * ``LessThanThreshold``
          * ``LessThanOrEqualToThreshold``
