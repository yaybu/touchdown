Tailing logs
============

You can tail your logs with the ``tail`` command.

For example if you have a CloudWatch log group defined::

    aws.add_log_group(
        name="application.log",
    )

Then you could get the last 15 minutes of log events with::

    touchdown tail application.log -s 15m

And you could stream the logs as they are ingested with::

    touchdown tail application.log -f


You can use the following arguments:

.. program:: touchdown tail

.. option:: --start, -s

    The time to start fetching logs from.

.. option:: --end, -e

    The time to fetch logs until.

.. option:: --follow, -f

    Don't exit. Continue to monitor the log stream for new events.
