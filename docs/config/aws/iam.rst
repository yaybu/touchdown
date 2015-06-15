Identity & Access Management
============================

.. module:: touchdown.aws.iam
   :synopsis: Identity & Access Management resources.


PasswordPolicy
--------------

.. class:: PasswordPolicy

    You can set password policy on an Amazon account resource::

        aws.add_password_policy(
            min_password_length=16,
        )

    .. attribute:: min_password_length

    .. attribute:: require_symbols

    .. attribute:: require_numbers

    .. attribute:: require_uppercase

    .. attribute:: require_lowercase

    .. attribute:: allow_users_to_change_password

    .. attribute:: expire_passwords

    .. attribute:: max_password_age

    .. attribute:: password_reuse_prevention

        Must be between 1 and 24.

    .. attribute:: hard_expiry


InstanceProfile
---------------

.. class:: InstanceProfile

    You can create an ``InstanceProfile`` from an amazon account resource::

        instance_profile = aws.add_instance_profile(
            name="my-instance-profile",
            roles=[my_role],
        )

    .. attribute:: name

    .. attribute:: path

    .. attribute:: roles

        A list of :class:`Role` resources.


Role
----

.. class:: Role

    You can create a ``Role`` from an amazon account resource::

        role = aws.add_role(
            name="my-role",
            policies = {
                "s3-access": {
                    # ... IAM policy definition ...
                }
            }
        )

    .. attribute:: name

    .. attribute:: path

    .. attribute:: assume_role_policy

        This field is a policy that describes who or what can assume this role.
        For example, if this is a role for EC2 instances you could set it to::

            aws.add_role(
                name="my-role"
                assume_role_policy={
                    "Statement": [{
                        "Effect": "Allow",
                        "Principal": {"Service": ["ec2.amazonaws.com"]},
                        "Action": ["sts:AssumeRole"],
                    }],
                },
            )

    .. attribute:: policies

        A dictionary of policies that apply when assuming this role.


ServerCertificate
-----------------

.. class:: ServerCertificate

    In order to use SSL with a :class:`touchdown.aws.cloudfront.Distribution`
    or a :class:`touchdown.aws.elb.LoadBalancer` you'll first need to upload
    the SSL certificate to IAM with the ``ServerCertificate`` resource.

    .. attribute:: name

    .. attribute:: path

    .. attribute:: certificate_body

    .. attribute:: certificate_chain

    .. attribute:: private_key
