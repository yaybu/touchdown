Hello world: A static site with S3, Route53 and CloudFront
==========================================================

Here is a simple ``Touchdownfile`` that creates a bucket and sets up Route53
DNS for it::

    aws = workspace.add_aws(
        access_key_id='AKI.....A',
        secret_access_key='dfsdfsdgrtjhwluy52i3u5ywjedhfkjshdlfjhlkwjhdf',
        region='eu-west-1',
    )

    bucket = aws.add_bucket(
        name="example.com",
    )

    hosted_zone = aws.add_hosted_zone(
        name="example.com",
        records=[{
            "type": "A",
            "alias": bucket,
        }]
    )

All configurations start at the workspace object.

We ask the workspace for an AWS account for a given set of credentials and for
a specific region.

To that AWS account we add a bucket to store our static website.

Then we add a Route53 zone. We pass in the bucket to the ``alias`` parameter.
Alias records are a bit like server-side ``CNAMES``.
You can pass any resource to the ``alias`` parameter that has a hosted zone id.
See the :class:`~touchdown.aws.route53.HostedZone` documentation for the full
list.

From this configuration Touchdown knows it must create a bucket before it can
update the hosted zone. And it knows it must have perform any account setup
steps before it can touch the bucket or hosted zone.
