Web Application Firewall
========================

.. module:: touchdown.aws.waf
   :synopsis: Configure and deploy a WAF for applications using CloudFront


Amazon provide a Web Application Firewall for your CloudFront Web Distributions. At 'layer 7' it is able to inspect HTTP traffic passing through CloudFront and block malicious signatures or even just provide IP filtering that is URI specific.


How do I create an IP whitelist for my staging environment?
-----------------------------------------------------------

Let's say your office IP address is 8.8.8.8. You need to create an `ip_set` with the addresses that are allowed to access your staging environment::

    ip_set = self.aws.add_ip_set(
        name="site-access-permitted",
        addresses=[
            "8.8.8.8/32",
        ],
    )

We add a `rule` that says matches all addresses in that set. With no other ``predicates`` defined this will match all HTTP traffic from the addresses in the set::

    authorized_access = self.aws.add_rule(
        name="authorized-access",
        predicates=[{"ip_set": ip_set}],
        metric_name="AuthorizedAccess",
    )

The final step is to add this to a web_acl and tell WAF that the rule should ``ALLOW`` traffic matching it, and all other traffic should be blocked::

    staging_firewall = self.aws.add_web_acl(
        name="staging-firewall",
        activated_rules=[{
            "rule": authorized_access,
            "priority": 1,
            "action": "ALLOW",
        }],
        default_action="BLOCK",
        metric_name="MyWafRules",
    )

If you are using Touchdown to manage your CloudFront distribution you can use the ``web_acl`` attribute to link it all up::

    self.aws.add_distribution(
        name="www.example.com",
        web_acl=my_web_acl,
    )


How do I IP restrict my admin interface?
----------------------------------------

Let's say your admin interface is located at `/admin` and your office IP address is 8.8.8.8. You need to create a byte_match to match requests for the URI and an ip_set to match your office IP::

    byte_match_set = self.aws.add_byte_match_set(
        name="dashboard-access",
        byte_matches=[{
            "field": "URI",
            "transformation": "URL_DECODE",
            "position": "STARTS_WITH",
            "target": "/admin/",
        }],
    )

    ip_set = self.aws.add_ip_set(
        name="dashboard-access-permitted",
        addresses=[
            "8.8.8.8/32",
        ],
    )

And we want to match requests that *aren't* from our `ip_set` but do match our `byte_match_set`::

    unauthorised_admin_access = self.aws.add_rule(
        name="unauthorized-admin-access",
        predicates=[
            {
                "ip_set": ip_set,
                "negated": True,
            },
            {
                "byte_match_set": byte_match_set,
            }
        ],
        metric_name="UnauthorizedAdminAccess",
    )

The final step is to add this to a web_acl and tell WAF that the rule should ``BLOCK`` traffic matching it::

    my_web_acl = self.aws.add_web_acl(
        name="my-waf-rules",
        activated_rules=[{
            "rule": unauthorised_admin_access,
            "priority": 1,
            "action": "BLOCK",
        }],
        default_action="ALLOW",
        metric_name="MyWafRules",
    )


Web ACL
-------

.. class:: WebACL

    To create a Web ACL you need to specify at least its ``name``, ``metric_name`` and ``default_action``::

        web_acl = aws.add_web_acl(
            name='my-webacl',
            metric_name='MyWebACL',
            default_action='BLOCK',
        )

    .. attribute:: name

        The name of the Web ACL. This field is required.

    .. attribute:: activated_rules

        A list of rules that apply to this ACL. The following 3 fields must be set:

            ``rule``
                A :py:class:~`Rule`.
            ``priority``
                Rules with lower ``priority`` are evaluated before rules with a higher ``priority``.
            ``action``
                Must be one of ``ALLOW``, ``BLOCK`` or ``COUNT``.

    .. attribute:: default_action

        The default action to take if no rules in ``activated_rules`` have matched the request. Must be one of ``ALLOW`` or ``BLOCK``.

    .. attribute:: metric_name

        A CloudWatch metric name.


Rule
----

.. class:: Rule

    To create a WAF Rule you need to specify its ``name`` and a ``metric_name``::

        rule = aws.add_rule(
            name='my-waf-rule',
            metric_name='MyWafRule',
        )

    .. attribute:: name

    .. attribute:: metric_name


IP Set
------

.. class:: IPSet

    To get started with IP sets you at least need to give it a ``name``::

        ips = aws.add_ip_set(
            name='my-ips',
        )

    .. attribute:: name

        The name of the ip_set. This must be unique within a region.

    .. attribute:: addresses

        A list of IP networks to match against::

            ips = aws.add_ip_set(
                name='my-ips',
                addresses=[
                    '8.8.8.8/32',
                ]
            )

        As a CloudFront distribution can only be accessed from the public internet these should be public addresses. IP's in the following networks are not valid:

          * ``10.0.0.0/8``
          * ``172.16.0.0/12``
          * ``192.168.0.0/16``


Byte Match Set
--------------

.. class:: ByteMatchSet

    To create a byte match set you need to at least gitve it a ``name``::

        byte_matches = aws.add_byte_match_set(
            name='my-byte-matches',
        )

    .. attribute:: name

        The name of the byte_match_set. This must be unique within a region.

    .. attribute:: byte_matches

        A list of data to match against::

        byte_matches = aws.add_byte_match_set(
            name='my-byte-matches',
            byte_matches=[{
                "field": "URI",
                "transformation": "URL_DECODE",
                "position": "STARTS_WITH",
                "target": "/admin/",
            }],
        )

        .. attribute:: field

            Must be one of:

                ``URI``
                ``QUERY_STRING``
                ``HEADER``
                ``METHOD``
                   Use this to limit your matches to a ``GET`` or ``POST`` method, etc.
                ``BODY``
                   Match against the first 8192 bytes of he body of the request.

        .. attribute:: header

            You can only use this attribute if ``field`` is set to ``HEADER``.

        .. attribute:: transformation

            A transformation to apply before comparing the selected ``field`` to ``target``.

            Must be one of:

                ``CMD_LINE``
                ``COMPRESS_WHITE_SPACE``
                ``HTML_ENTITY_DECODE``
                ``LOWERCASE``
                ``URL_DECODE``
                ``NONE``
                    Don't apply any transformations to the string before matching against it.

            The default value is ``NONE``.

        .. attribute:: position

            Where in the chosen ``field`` to look for ``target``. Must be one of:

                ``CONTAINS``
                ``CONTAINS_WORD``
                ``EXACTLY``
                ``STARTS_WITH``
                ``ENDS_WITH``

        .. attribute:: target

            Some byte data to look for in the chosen ``field`` after applying a ``transformation``. Must be between 1 and 50 bytes.
