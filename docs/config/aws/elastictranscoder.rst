==================
Elastic Transcoder
==================

.. module:: touchdown.aws.elastictranscoder
   :synopsis: Elastic Transcoder resources.


Pipeline
========

.. class:: Pipeline

    ..attribute:: name

        The name of the pipeline. This field is required.

    ..attribute:: input_bucket

        A :class:`~touchdown.aws.s3.Bucket`.

    ..attribute:: output_bucket

        A :class:`~touchdown.aws.s3.Bucket`.

    ..attribute:: role = argument.Resource(Role, field="Role")

        A :class:`~touchdown.aws.iam.Role`.

    ..attribute:: key

        A KMS key. Not currently supported.

    ..attribute:: notifications

        An SNS notification topic. Not currently supported.

    ..attribute:: content_config

    ..attribute:: thumbnail_config
