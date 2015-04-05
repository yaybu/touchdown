.. currentmodule: touchdown.aws

Authentication
==============

Access to AWS services is authenticated used a pair of credentials called the
``access_key_id`` and the ``secret_access_key``. A single user account can have
multiple access keys associated with it, and via the STS service you can
generate access keys directly for a role (rather than for a user).


Access keys
-----------

The simplest way to start performing actions against AWS is to add a
:class:`~touchdown.aws.account.Account` object to your workspace::

    aws = workspace.add_aws(
        access_key_id='AKIDFKJDKFJF',
        secret_access_key='skdfkoeJIJE4e2SFF',
        region='eu-west-1',
    )

If you will be orchestrating AWS services from within AWS you can use a
:class:`touchdown.aws.iam.InstanceProfile` to grant temporary credentials to an
EC2 instance. Touchdown will automatically retrieve them from the AWS metadata
service when you don't specify an ``access_key_id``:

    aws = workspace.add_aws(
        region='eu-west-1',
    )


Assuming a role
---------------

If you have multiple accounts at Amazon (perhaps one per customer) and have a
shared resource - such as a Route53 zone - then you can use cross-account roles
to manage it.

In the account with the shared resource you can create a role as follows::

    aws.add_role(
        name="route53_full_access_{}".format(env.environment),
        assume_role_policy={
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"AWS": "arn:aws:iam::{}:root".format(env.account)},
                "Action": "sts:AssumeRole"
            }]
        },
        policies={
            "route53_full_access": {
                "Statement": [{
                    "Effect": "Allow",
                    "Action": ["route53:*"],
                    "Resource": ["*"]
                }]
            }
        },
    )


Now in your other account you can assume this role::

    other_account = aws.add_external_role(
        name='my-role',
        arn='',
    )

    other_account.add_hosted_zone(
        name='www.example.com',
    )
