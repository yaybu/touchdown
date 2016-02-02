Amazon Certificate Manager
==========================

.. module:: touchdown.aws.acm
   :synopsis: Automated management of DV SSL certificates

Amazon Certificate Manager generates free certificates for TLS with Elastic Load Balancer and CloudFront, and transparently handles rotation and renewal.

When you request a certificate Amazon validate you control the domain by e-mail. For example if you requested a certificate for ``www.example.com`` it attempts to contact:

 * The domain registrant
 * The technical contact
 * The administrative contact
 * ``admin@www.example.com``
 * ``administrator@www.example.com``
 * ``hostmaster@www.example.com``
 * ``postmaster@www.example.com``
 * ``webmaster@www.example.com``

.. note::

    These certificates can only be used with Amazon services - there is no way to obtain the private certificate.


If you already have a certificate that you wish to use with CloudFront or ELB you can upload it with a :py:class:`~touchdown.aws.iam.server_certificate.ServerCertificate`.


Creating a certificate
----------------------

.. class:: Certificate

    To create a certificate you just need to choose the domain it is for::

        certificate = aws.add_acm_certificate(
            name='www.example.com',
        )

    .. attribute:: name

        The domain name to request a certificate for.

    .. attribute:: validation_options

        By default ACM will e-mail the contacts for your domain - so `hostmaster@www.example.com` in the previous example. You can override this::

            certificate = aws.add_acm_certificate(
                name="www.example.com",
                validation_options=[{
                    "domain": "www.example.com",
                    "validation_domain": "example.com",
                }]
            )

    .. attribute:: alternate_names

        A list of alternative domain names this cert should be valid for, for example for ``www.example.com`` you might also add ``www.example.net``.
