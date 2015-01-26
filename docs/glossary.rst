Glossary
=========

.. glossary::

   goal
       A goal is a state that touchdown should aim to achieve. For example,
       the "destroy" goal will cause Touchdown to generate a plan to tear down
       the environment.

   plan
       Given a :term:`goal` and a :term:`resource` a plan decides what changes
       need to be made to achieve the goal.

   resource
       An entity that is subject to configuration management by Touchdown. It
       has a type, such as :class:`~touchdown.aws.elb.LoadBalancer`, and a set
       of properties that should be applied to it.
