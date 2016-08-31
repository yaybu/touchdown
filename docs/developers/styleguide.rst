Style Guide
===========

Automatic style checks
----------------------

All code merged to master **must**:

 * Pass all default flake8 checks. Absolutely none of them are turned off.
 * Use only single quote python strings (enforced by flake8-quotes).
 * Have correctly sorted imports (enforced by flake8-isort).
 * Have reasonably low cyclomatic complexity (mccabe set to ``11``).
 * Have a maximum line length of 151.

CI will not pass unless these are met, and that is a requirement for any PR.


Style examples
--------------

Imports
~~~~~~~

Imports should be grouped. Standard library modules are always first, followed by third party as a separate block. The final block touchdown modules. For example::

    import datetime
    import logging
    import time

    import jmespath
    from botocore.exceptions import ClientError

    from touchdown.core import errors, resource, serializers
    from touchdown.core.action import Action
    from touchdown.core.plan import Present

This is enforced by ``flake8-isort``, which picks up its settings from ``setup.cfg``.


Function calls, lists and dictionaries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a function, list or dict neatly fits on one line it should be formatted on one line::

    foo = myfunction('abc', {'myarg': 'myvalue'})

If it does not then the preferred way to split it ups is::

    foo = myfunction('abc', {
        'myarg1': 'myvalue',
        'myarg2': 'myvalue',
        'myarg3': 'myvalue',
        'myarg4': 'myvalue',
    })

The closing brackets are inline with the indentation of `foo = `.

This is quote common when defining resources::

    class Policy(Resource):

        resource_name = 'policy'

        name = argument.String(field='PolicyName')
        adjustment_type = argument.String(
            choices=['ChangeInCapacity', 'ExactCapacity', 'PercentChangeInCapacity'],
            default='ChangeInCapacity',
            field='AdjustmentType'
        )
