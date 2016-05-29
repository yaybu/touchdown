Lambda
======

.. module:: touchdown.aws.lambda_
   :synopsis: Executing code units on AWS infrastructure without managing servers


Function
--------

.. class:: Function

    You can register a lambda function against an Amazon account resource::

        def hello_world(event, context):
            print event

        aws.add_lambda_function(
            name = 'myfunction',
            role = aws.add_role(
                name='myrole',
                #..... snip ....,
            ),
            code=hello_world,
            handler="main.hello_world",
        )

    .. attribute:: name

        The name for the function, up to 64 characters.

    .. attribute:: description

        A description for the function. This is shown in the AWS console and API but is not used by lambda itself.

    .. attribute:: role

        A :class:`~touchdown.aws.iam.Role` resource.

        The IAM role that Lambda assumes when it executes your function to access any other Amazon Web Services (AWS) resources.

    .. attribute:: code

        A python callable. For example::

            def hello_world(event, context):
                print event

            aws.add_lambda_function(
                name='hello_world',
                code=hello_world,
                handler='main.hello_world'
                ...
            )

        It must take 2 arguments only - ``event`` and ``context``.

        This is intended for proof of concept demos when first starting out with lambda - there is no mechanism to ship dependencies of this function, it is literally the output of `inspect.getsource()` that is uploaded.

    .. attribute:: code_from_bytes

    .. attribute:: code_from_s3

        An S3 :py:class:`~touchdown.aws.s3.file.File`.

        A new version of the lambda function is published when touchdown detects that the date/time stamp of this file is newer than the last modified stamp on the lambda function.

    .. attribute:: handler

        The entry point to call.

        For the ``python2.7`` runtime with a ``shrink_image.py`` module containing a function called ``handler`` the handler would be ``shrink_image.handler``.

        For the ``node`` runtime with a ``CreateThumbnail.js`` module containing an exported function called ``handler``, the handler is ``CreateThumbnail.handler``.

        For the ``java8`` runtime, this would be something like ``package.class-name.handler`` or just ``package.class-name``.

    .. attribute:: timeout

        An integer. The number of seconds (between 1 and 300) that a lambda function is allowed to execute for before it is interrupted. The default is 3 seconds.

    .. attribute:: memory

        The amount of RAM your lambda function is given. The amount of CPU is assigned based on this as well - more RAM means more CPU is allocated.

        The default value is 128mb, which is also the minimum. Can assign up to 1536mb.

    .. attribute:: publish
