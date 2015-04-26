Key management service
======================

.. module:: touchdown.aws.kms
   :synopsis: Key management service resources.


The Key Management Service is a scaled and highly available API for managing
encryption keys.

It is integrated with:

 * RDS
 * S3
 * EBS
 * Redshift
 * EMR
 * Elastic Transcoder
 * WorkMail

With KMS you can create keys that can never be exported from the service and
restrict encryption and decryption by IAM policy.


.. class:: Key

    A key in the Amazon KMS service.

    ..warning:: A key cannot be directly named.

        Without a name there would be no way for touchdown to remember which
        key it created previously (without out-of-band state). In order to
        idempotently manage a key we effectively use the description
        field as a name field.

    .. attribute:: description

        The description of the key. Must be at most 8192 characters.

    .. attribute:: usage

        Currently this field can only be set to ``ENCRYPT_DECRYPT`` (which is
        the default).

    .. attribute:: policy

        An IAM policy describing which users can access this key.


.. class:: Alias

    An alias for referring to a KMS key.

    .. attribute:: name

        A name to refer to this alias by.

    .. attribute:: key

        A :class:`Key` to point this alias at.
