CloudFront
==========

.. module:: touchdown.aws.cloudfront
   :synopsis: CloudFront resources.

There are 2 kinds of CloudFront distribution:

 * A 'Web' distribution that acts as a CDN for HTTP and HTTPS traffic
 * A 'Streaming' distribution that acts as a CDN for RTMP traffic


Serving content over HTTP and HTTPS
-----------------------------------

Web distributions act an "origin pull" based content delivery network. This
means they work a bit like a caching proxy like varnish.

There are several pieces that need configuring. Together these pieces are
called a Distribution Config. They are:

  * How should the distribution listen for traffic. What ports, what certs,
    what domains.
  * What backend servers can traffic be sent to. These are origins.
  * How should traffic be mapped from a request to an origin. For example, you
    might have a application cluster at ``/`` and a search cluster at
    ``/search``. These are called cache behaviours, and can also change how
    aggressively you cache based on the URL.

.. note:: CloudFront configuration changes are slow

    Any configuration changes to a distribution are slow - taking around 15
    minutes. If using blue/green type techniques during deployment it is best
    to not do that switch at the CloudFront tier of your stack.

.. class:: Distribution

    The minimum distribution is::

        distribution = self.aws.add_distribution(
            name='www.example.com',
            origins=[{
                "name": "www",
                "domain_name": "backend.example.com",
            }],
            default_cache_behavior={
                "target_origin": "www",
            },
        )

    .. attribute:: name

        The name of the distribution. This should be the primary domain that it
        responds to.

    .. attribute:: comment

        Any comments you want to include about the distribution.

    .. attribute:: aliases

        Alternative domain names that the distribution should respond to.

    .. attribute:: root_object

        The default URL to serve when the users hits the root URL. For example
        if you want to serve index.html when the user hits www.yoursite.com
        then set this to '/index.html'. The default is '/'

    .. attribute:: enabled

        Whether or not this distribution is active. A distribution must be
        enabled before it can be accessed by a client. It must be disabled
        before it can be deleted.

    .. attribute:: origins

        A list of :class:`Origin` resources that the Distribution acts as a
        front-end for.

    .. attribute:: default_cache_behavior

        How the proxy should behave when none of the rules in ``behaviors``
        have been applied.

    .. attribute:: behaviors

        A list of :class:`CacheBehavior` rules about how to map incoming
        requests to ``origins``.

    .. attribute:: error_responses

        A list of :class:`ErrorResponse` rules that customize the content
        that is served for various error conditions.

    .. attribute:: logging

        A :class:`LoggingConfig` resource that describes how CloudFront
        should log.

    .. attribute:: price_class

        The price class. By default ``PriceClass_100`` is used, which is the
        cheapest.

    .. attribute:: ssl_certificate

        A :class:`~touchdown.aws.iam.ServerCertificate`.

    .. attribute:: ssl_support_method

        If this is set to ``sni-only`` then CloudFront uses the SNI mechanism.
        This only works on browsers newer than IE6. If you need maximum
        compatibility set it to ``vip``. Your distribution will be assigned its
        own dedicated IP addresses, negating the need to use SNI. However, this
        is much more expensive.

    .. attribute:: ssl_minimum_protocol_version

        The default value is ``TLSv1``. To decrease the security of your system
        you can instead set this to ``SSLv3``. **This is strongly discouraged**.


Serving content from an S3 bucket
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can pass a :class:`S3Origin` to a CloudFront distribution to have it serve
content from an S3 bucket. If you have a bucket called ``my-test-bucket`` then
this looks like::

    bucket = aws.add_bucket(name="my-test-bucket")

    distribution = self.aws.add_distribution(
        name='www.example.com',
        origins=[{
            "name": "www",
            "bucket": bucket,
        }],
        default_cache_behavior={
            "target_origin": "www",
        },
    )

You cannot use SSL for an S3 bucket backend - even if using HTTPS between the
client and CloudFront, the connection between CloudFront and S3 will always be
over unencrypted HTTP.

.. class:: S3Origin

    .. attribute:: name

        A name for this backend service. This is used when defining cache
        behaviors.

    .. attribute:: bucket

        A :class:`~touchdown.aws.s3.Bucket` to serve content from.

    .. attribute:: origin_access_identity


Serving content from a backend HTTP or HTTPS service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CloudFront can act as a proxy for any HTTP or HTTP service. Just pass a
:class:`CustomOrigin` to a CloudFront distribution. For example, to serve
content from ``backend.example.com`` on port 8080 abd 8443::

    distribution = self.aws.add_distribution(
        name='www.example.com',
        origins=[{
            "name": "www",
            "domain_name": "backend.example.com",
            "http_port": 8080,
            "https_port": 8043,
        }],
        default_cache_behavior={
            "target_origin": "www",
        },
    )


.. class:: CustomOrigin

    .. attribute:: name

        A name for this backend service. This is used when defining cache
        behaviors.

    .. attribute:: domain_name

        A backend server to contact.

    .. attribute:: http_port

        The port that is serving HTTP content. The default value is ``80``.

    .. attribute:: https_port

        The port that is serving HTTPS content. The default value is ``443``.

    .. attribute:: protocol

        Specifies what protocol is used to contact this origin server. The
        default is ``match-viewer``. This means that the backend is contacted
        with TLS if your client is using https. A less secure option is
        ``http-only`` which can be used to send even secure and confidential
        traffic in the clear to your backend.

    .. attribute:: ssl_policy

        Specifies the permitted backend ssl versions. Defaults to SSLv3 and TLSv1.


Cache behaviours
~~~~~~~~~~~~~~~

Particularly if you are using CloudFront in front of your entire site you might
want different caching policies from different URL's. For example, there is no
need to pass the query string or any cookies to the part of your site that
serves CSS. This helps to improve cacheability.


.. class:: CacheBehavior

    .. attribute:: target_origin

        The name of a :class:`S3Origin` or :class:`CustomOrigin` that this
        behaviour applies to.

    .. attribute:: forward_query_string

        Whether or not to forward the query string to the origin server.

    .. attribute:: forward_headers

        A whitelist of HTTP headers to forward to the origin server.

        If you want to forward all headers you can set this to ``['*']``. If
        you set it to an empty list no headers will be sent.

    .. attribute:: forward_cookies

        A list of cookies to forward to the origin server.

        If you want to forward all cookies you can set this to ``['*']``. If you
        set it to an empty list no cookies will be sent.

    .. attribute:: viewer_protocol_policy

        If set to ``https-only`` then all traffic will be forced to use TLS.
        If set to ``redirect-to-https`` then all HTTP traffic will be
        redirected to the https version of the url. ``allow-all`` passes on
        traffic to the origin using the same protocol as the client used.

    .. attribute:: default_ttl

    .. attribute:: min_ttl

        The minimum amount of time to cache content for.

    .. attribute:: max_ttl

    .. attribute:: allowed_methods

        The HTTP methods that are passed to the backend.

    .. attribute:: cached_methods

        The HTTP methods that might be cached. For example, it's unlikely that
        you would ever cache a ``POST`` request.

    .. attribute:: smooth_streaming

        Whether or not to turn on smooth streaming.


Error handling
~~~~~~~~~~~~~~

.. class:: ErrorResponse

    .. attribute:: error_code

        A HTTP error code to replace with static content. For example, ``503``.

    .. attribute:: response_page_path

        A page to serve from your domain when this error occurs. If ``/`` was
        served by your application and ``/static`` was served from S3 then you
        would want to serve the page from ``/static``, otherwise it is likely
        your error page would go down when your site went down.

    .. attribute:: response_code

        By default this is the same as the ``error_code``. However you can
        transform it to a completely different HTTP status code - even ``200``!

    .. attribute:: min_ttl

        How long can this error be cached for? It can be useful to set this to
        a low number for very busy sites - as it can act as a pressure release
        valve. However it is safest to set it to 0.


Access logging
~~~~~~~~~~~~~~

.. class:: LoggingConfig

    CloudFront can log some information about clients hitting the CDN and sync
    those logs to an S3 bucket periodically.

    .. attribute:: enabled

        By default this is ``False``. Set it to ``True`` to get CDN logs.

    .. attribute:: include_cookies

        Set to ``True`` to include cookie information in the logs.

    .. attribute:: bucket

        A :class:`~touchdown.aws.s3.Bucket`.

    .. attribute:: path

        A path within the S3 bucket to store the incoming logs.


Serving media over RTMP
-----------------------

A streaming distribution allows you to serve static media to your visitors over
RTMP. You will need to serve the media player over HTTP(S) so you will probably
use a streaming distribution in conjunction with a standard CloudFront
distribution.

RTMP requests are accepted on ports 1935 and port 80. This is not configurable.

CloudFront supports:

 * RTMP
 * RTMPT (RTMP over HTTP)
 * RTMPE (Encrypted RTMP)
 * RTMPTE (Encrypted RTMP over HTTP)


.. class:: StreamingDistribution

    .. attribute:: name

        The name of the streaming distribution. This should be the primary
        domain that it responds to.

    .. attribute:: comment

        Any comments you want to include about the distribution.

    .. attribute:: aliases

        Alternative names that the distribution should respond to.

    .. attribute:: enabled

        Whether or not this distribution is active.

    .. attribute:: origin

        A :class:`S3Origin` that describes where to stream media from.

    .. attribute:: logging

        A :class:`StreamingLoggingConfig` resource that describes how CloudFront
        should log.

    .. attribute:: price_class

        The price class. By default ``PriceClass_100`` is used, which is the
        cheapest.


.. class:: StreamingLoggingConfig

    .. attribute:: enabled

        By default this is ``False``. Set it to ``True`` to get CDN logs.

    .. attribute:: bucket

        A :class:`~touchdown.aws.s3.Bucket`.

    .. attribute:: path

        A path within the S3 bucket to store the incoming logs.
