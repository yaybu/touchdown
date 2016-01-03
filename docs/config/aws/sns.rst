Simple Notification Service
===========================

.. module:: touchdown.aws.sns
   :synopsis: Simple Notification Service.

Simple Notification Service is a managed push notification service.

It can push notifications to:

 * HTTP endpoints
 * Amazon SQS :class:`~touchdown.aws.sqs.Queue`'s
 * Amazon Lambda :class:`~touchdown.aws.lambda_.Function`'s
 * SMS text messages
 * E-mail
 * Apple, Android, Fire OS and Window devices

Messages published to SNS are stored redundantly to prevent messages being lost.

.. note:: Accessing this service requires internet access.

    If you want to access this from an EC2 you must either:

      * Give the node a public IP and connect its route table to an internet gateway
      * Set up NAT
      * Set up a proxy cluster


.. class:: Topic

    An SNS topic.

    Can be added to any account resource::

        topic = aws.add_topic(
            name='my-bucket',
        )

    .. attribute:: name

        The name of the bucket. This field is required, and it must be unique
        for the whole of Amazon AWS.

    .. attribute:: notify

        A list of resources that should be subscribed to this topic. Can be any
        of:

            * :class:`~touchdown.aws.sqs.Queue`
            * :class:`~touchdown.aws.lambda_.Function`

    .. attribute:: display_name

    .. attribute:: policy

    .. attribute:: delivery_policy
