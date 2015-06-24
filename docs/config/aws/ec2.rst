Elastic Compute Cloud
=====================

.. module:: touchdown.aws.ec2
   :synopsis: Elastic Compute Cloud resources.


EC2 is the main workhorse of an AWS solution. It allows you to (manually or
automatically) start virtual machines to run your application code.

.. note:: We recommend that your EC2 machines are stateless.


Machine Images
--------------

.. class:: Image

    This represents a virtual machine image that can be used to boot an EC2
    instance.

    .. attribute:: name

    .. attribute:: description

    .. attribute:: source_ami

        An AMI to base the new AMI on.

    .. attribute:: username

        The username to use when sshing to a new images.

    .. attribute:: steps

        A list of steps to perform on the booted machine.

    .. attribute:: launch_permissions

    .. attribute:: tags


Key Pair
--------

.. class:: KeyPair

    In order to securely use SSH with an EC2 instance (whether created directly
    or via a AutoScalingGroup) you must first upload the key to the EC2 key
    pairs database. The KeyPair resource imports and keeps up to date an ssh
    public key.

    It can be used with any AWS account resource::

        aws.add_keypair(
            name="my-keypair",
            public_key=open(os.expanduser('~/.ssh/id_rsa.pub')),
        )

    .. attribute:: name

        The name of the key. This field is required.

    .. attribute:: public_key

        The public key material, in PEM form. Must be supplied in order to
        upload a key pair.
