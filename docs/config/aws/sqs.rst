Simple Queue Service
====================

.. module:: touchdown.aws.sqs
   :synopsis: Simple Queue Service.

Simple Queue Service is a managed queue service.

It is considered to be engineered for redundancy, so you do not need to set up
extra queues for availabilty.

.. note:: Accessing this service requires internet access.

    If you want to access this from an EC2 you must either:

      * Give the node a public IP and connect its route table to an internet gateway
      * Set up NAT
      * Set up a proxy cluster


.. class:: Queue

    An SQS Queue.

    Can be added to any account resource::

        queue = aws.add_queue(
            name='my-queue',
        )

    .. attribute:: name

        The name of the queue.

    .. attribute:: delay_seconds

        An integer between 0 and 900.

    .. attribute:: maximum_message_size

        An integer between 1024 and 252144.

    .. attribute:: message_retention_period

        An integer between 60 and 1209600

    .. attribute:: policy

    .. attribute:: receive_message_wait_time_seconds

        An integer between 0 and 20.

    .. attribute:: visibility_timeout

        An integer between 0 and 43200. The default is 30.
