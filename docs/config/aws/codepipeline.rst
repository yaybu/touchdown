CodePipeline
============

.. module:: touchdown.aws.codepipeline
   :synopsis: Continuous deployment


Why should I use CodePipeline?
-----------------------------

CodePipeline provides the building blocks for continuous deployment pipelines.
It allows you to set up chains of steps that should be executed after a commit
is detected in your version control system. For example, your pipeline might:

 * Wait for changes in a GitHub repository
 * Build an AMI from the commit
 * Deploy the AMI to a staging environment
 * Run some automated tests against the environment
 * Deploy the AMI to your production environment

If this is the kind of process you want for your infrastructure CodePipeline may
be the tool for you.

.. note:: CodePipeline is currently only available in ``us-east-1``.


Setting up a pipeline
---------------------

.. class:: Pipeline

    .. attribute:: name

        A name for this Pipeline. This field is required.

    .. attribute:: blockers

    .. attribute:: actions
