============================
Identity & Access Management
============================

.. module:: touchdown.aws.iam
   :synopsis: Identity & Access Management resources.


InstanceProfile
===============

.. class:: InstanceProfile

    .. attribute:: name

    .. attribute:: path

    .. attribute:: roles

        A list of :class:`Role` resources.


Role
====

.. class:: Role

    .. attribute:: name

    .. attribute:: path

    .. attribute:: assume_role_policy

        This field is a policy that describes who or what can assume this role.

    .. attribute:: policies

        A dictionary of policies that apply when assuming this role.


ServerCertificate
=================

.. class:: ServerCertificate

    In order to use SSL with a :class:`touchdown.aws.cloudfront.Distribution`
    or a :class:`touchdown.aws.elb.LoadBalancer` you'll first need to upload
    the SSL certificate to IAM with the ``ServerCertificate`` resource.

    .. attribute:: name

    .. attribute:: path

    .. attribute:: certificate_body

    .. attribute:: certificate_chain

    .. attribute:: private_key
