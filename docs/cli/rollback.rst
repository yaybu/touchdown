Rolling back your data
======================

You can rollback your application state with the ``rollback`` command.

For example, if you have an Amazon RDS database called ``foo`` you can rollback the last 15m of changes with::

    touchdown rollback foo 15m

Or you could revert it to a named snapshot with::

    touchdown rollback foo mysnapshot
