Getting signon urls
===================

Some services support generating urls for granting secure temporary access to
their admin interfaces. For example, you can generate an AWS federation URL
for any IAM Role that you can assume. Touchdown exposes this via its
``get-signin-url`` command. For example, for an AWS
:class:`~touchdown.aws.iam.Role` defined like this::

    aws.add_role(
        name="deployment",
        assume_role_policy={...},
        policies={...},
    )

You can::

    touchdown get-signin-url deployment

To get a url that allows you to see the AWS console with just the policies
attached to that role.
