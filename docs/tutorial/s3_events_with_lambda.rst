Handling S3 events with lambda functions
========================================

Suppose you store incoming media (such as .jpg or .png) in an incoming bucket and want to resize it into an output bucket. In this walkthrough we will use AWS Lambda to perform the transformation automatically - triggered by S3 ``object-created`` events.

.. warning::

    This example assumes 2 separate buckets are used. Attempting to use one bucket will result in recursion.

First of all we need a function to handle the images. In this example we just copy them straight to the destination bucket, but you can easily add your own transformation logic. Because this function is entirely self contained it can live in your `Touchdownfile`::

    def resize_handler(event, context):
        import botocore.session
        session = botocore.session.get_session()
        s3 = session.create_client('s3', region_name='eu-west-1')
        for record in event['Records']:
            s3.copy_object(
                Bucket='resized',
                CopySource=record['s3']['bucket']['name'],
                Key=record['s3']['object']['key'],
            )

As it's an AWS example we need to setup an AWS workspace::

    aws = workspace.add_aws(
        access_key_id='AKI.....A',
        secret_access_key='dfsdfsdgrtjhwluy52i3u5ywjedhfkjshdlfjhlkwjhdf',
        region='eu-west-1',
    )

We need a role for lambda to use. These are the permissions that a lambda function will have. It **needs** access to push logs to CloudWatch logs. It needs access to read/write from our source and destination S3 buckets::

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

Then we can upload the actual lambda function. By default this will be a ``python2.7`` lambda function. Java and JavaScript can be uploaded as well, but you will need to set ``runtime``. If you set ``code`` to a callable, Touchdown will automatically generate a zip to upload::

    resize = aws.add_lambda_function(
        name="resize-media",
        role=resize_role,
        code=resize_handler,
        handler="main.resize_handler",
    )

We need a source bucket, and we need to set up `notify_lambda` to invoke our lambda function whenever any of the ``s3:ObjectCreated:*`` events happen::

    incoming = aws.add_bucket(
        name="incoming",
        notify_lambda=[{
            "name": "resize",
            "events": ["s3:ObjectCreated:*"],
            "function": resize,
        }],
    )

And we need an output bucket::

    resized = aws.add_bucket(
        name="resized",
    )
