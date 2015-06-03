Estimating cost
===============

You can estimate the cost of your configuration with the ``cost`` command.

    $ touchdown cost

This will output the prices for the instance sizes that you are using. This
means the time based cost for the resource and the cost per gigabyte.

.. warning::

    This is only a best-guess estimate. It doesn't consider bandwidth charges.
    It may also struggle with currency conversion, VAT and billing periods.

    This feature is **experimental**.
