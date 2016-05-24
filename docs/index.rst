=========
Touchdown
=========

Touchdown is a tool for launching and managing infrastructure services - be
they physical servers, virtual subnets or private dns records.

.. toctree::
   :hidden:

   overview
   installation
   cli/touchdown
   tutorial/index
   config/index
   framework


Getting started
===============

 * **From the top:**
   :doc:`Overview <overview>` |
   :doc:`Installation <installation>`

 * **CLI:**
   :doc:`The touchdown command <cli/touchdown>` |
   :doc:`Applying changes <cli/apply>` |
   :doc:`Tearing down environments <cli/destroy>` |
   :doc:`Viewing logs <cli/tail>` |
   :doc:`Snapshotting your data <cli/snapshot>` |
   :doc:`Rolling back data <cli/rollback>` |
   :doc:`SSHing to your infrastructure <cli/ssh>` |
   :doc:`SCPing to/from your infrastructure <cli/scp>` |
   :doc:`Estimating infrastructure cost <cli/cost>` |
   :doc:`Generating graphs <cli/dot>`

 * **Tutorial:**
   :doc:`Hello world <tutorial/hello_world>` |
   :doc:`Django <tutorial/django>` |
   :doc:`Handling S3 Events with Lambda <tutorial/s3_events_with_lambda>` |
   :doc:`A serverless redirect service <tutorial/redirects_with_apigateway>`


Resources
=========

 * **Amazon:**
   :doc:`Authentication <config/aws/authentication>` |
   :doc:`Autoscaling <config/aws/autoscaling>` |
   :doc:`Building serverless API's <config/aws/apigateway>` |
   :doc:`CDN <config/aws/cloudfront>` |
   :doc:`Compute <config/aws/ec2>` |
   :doc:`DNS <config/aws/route53>` |
   :doc:`Encryption Key Management <config/aws/kms>` |
   :doc:`Key Value Stores <config/aws/elasticache>` |
   :doc:`Identity & Access Management <config/aws/iam>` |
   :doc:`Lambda zero-admin compute <config/aws/lambda>` |
   :doc:`Load Balancing <config/aws/elb>` |
   :doc:`Monitoring <config/aws/cloudwatch>` |
   :doc:`Networking <config/aws/vpc>` |
   :doc:`Relational Databases <config/aws/rds>` |
   :doc:`Simple Notification Service <config/aws/sns>` |
   :doc:`Simple Queue Service <config/aws/sqs>` |
   :doc:`Simple Storage Service <config/aws/s3>` |
   :doc:`SSL Certificates <config/acm>` |
   :doc:`Transcoding <config/aws/elastictranscoder>` |
   :doc:`VPNs <config/aws/vpn>` |
   :doc:`Web Application Firewall <config/aws/waf>`

 * **Provisioning:**
   :doc:`Provisioner targets <config/provisioner/targets>` |
   :doc:`Deploying scripts <config/provisioner/bash>` |
   :doc:`Deploying fuselage bundles <config/provisioner/fuselage>`

 * **Notifications:**
   :doc:`Slack notifications <config/notifications/slack>` |
   :doc:`NewRelic deploy notifications <config/notifications/newrelic>`

 * **Tunables:**
   :doc:`Configuration <config/config>`


Getting help
============

 * Ask a question in the `#yaybu IRC channel`_.

 * Report a bug in our `issue tracker`_.

.. _#yaybu IRC channel: irc://irc.oftc.net/yaybu
.. _issue tracker: https://github.com/yaybu/touchdown/issues


Contributing
============
