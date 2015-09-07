Snapshotting your data
======================

You can snapshot your database with the ``snapshot`` command.

For example, if you have an Amazon RDS database called ``foo`` you can create a snapshot with::

    touchdown snapshot foo mysnapshot

You can then revert to it with::

    touchdown rollback foo mysnapshot
