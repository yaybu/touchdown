Estimating cost
===============

You can estimate the cost of your configuration with the ``cost`` command.

    $ touchdown cost

This will output the prices for the instance sizes that you are using. This
means the time based cost for the resource and the cost per gigabyte.

This command currently outputs an ASCII table::

    +----------------------------------+-----------------+
    | Resource                         | Cost (per hour) |
    +----------------------------------+-----------------+
    | load_balancer 'balancer'         | 0.028           |
    | database 'myapp          '       | 0.020           |
    | replication_group 'shared'       | 0.018           |
    | auto_scaling_group 'control'     | 0.028           |
    | auto_scaling_group 'nat'         | 0.014           |
    | auto_scaling_group 'worker'      | 0.028           |
    | auto_scaling_group 'schedule'    | 0.028           |
    | auto_scaling_group 'application' | 0.028           |
    +----------------------------------+-----------------+

.. warning::

    This is only a best-guess estimate. It doesn't consider bandwidth charges.
    It may also struggle with currency conversion, VAT and billing periods.

    This feature is **experimental**.
