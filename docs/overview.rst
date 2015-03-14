Overview
========

You can use Touchdown to build and manage infrastructure safely and repeatably.
It's python API can be used to describe the components of a simple hello world
application or an entire datacenter.

Touchdown is infrastructure as code. Whether you want disposable and repeatable
builds of a single application or to create a blueprint deployment strategy for
users of your web framework you can now treat it as another versionable
development artifact.

Using dependency information inferred from your configuration Touchdown can
generate efficient plans for creating new environments, updating existing ones
or tearing old ones down. You can see the changes it will make before it makes
them.

Under the hood this dependency information actually forms a graph. This enables
other features beyond just deploying configuration changes. Today we can
visualize your infrastructure to help you see how your components are
connected, but that is just the beginning.

Goals
-----

Strict
    It is frustrating and potentially even dangerous to have an operation fail
    part way through. It can be costly if it fails part way through a slow
    operation. So we do as much validation as possible before evening making the
    first API call.

Declarative
    The aim is to describe your environment in a declarative way. What should
    your infrastructure look like, not what changes to make to it. The metadata
    this gives about your environment is then useful for more than just creating
    an instance.

Idempotent
    Being able to run the tool twice and be confident that you won't end up
    with 2 semi-broken instances. Idempotence means it is safe to apply a
    configuration multiple times.

Repeatable
    Once your Touchdown configuration is working you should be able to tear it
    down and rebuild it, and get something configured exactly the same.


Direction
---------

The first phase of Touchdown is concentrating on building a solid foundation
with good support of Amazon technologies - from low level compute instances up
to the outward facing services like CloudFront.
