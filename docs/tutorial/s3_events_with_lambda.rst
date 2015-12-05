Handling S3 events with lambda functions
========================================

Suppose you store incoming media (such as .jpg or .png) in an incoming bucket and want to resize it into an output bucket. In this walkthrough we will use AWS Lambda to perform the transformation automatically - triggered by S3 ``object-created`` events.

.. warning::

    This example assumes 2 separate buckets are used. Attempting to use one bucket will result in recursion.

::

    aws = workspace.add_aws(
        access_key_id='AKI.....A',
        secret_access_key='dfsdfsdgrtjhwluy52i3u5ywjedhfkjshdlfjhlkwjhdf',
        region='eu-west-1',
    )

    resize_role = aws.add_role(
        name="resize-role",
        policies={
            "logs": {
                "Statement": [{
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Effect": "Allow",
                    "Resource": "arn:aws:logs:*:*:*"
                }]
            }
        },
        assume_role_policy={
            "Statement": [{
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }],
        },
    )

    resize = aws.add_lambda_function(
        name="resize-media",
        role=role,
        handler="main.resize_handler",
    )

    incoming = aws.add_bucket(
        name="incoming",
        notify_lambda=[{
            "name": "resize",
            "events": ["s3:ObjectCreated:*"],
            "function": resize,
        }],
    )

    resized = aws.add_bucket(
        name="resized",
    )
