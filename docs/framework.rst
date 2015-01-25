Framework
=========

Resource modelling
------------------

The core idea behind Touchdown is that you model your instrastructure with
"Resource" objects. These are declarative objects for describing your
instrastructure. Implementation wise they work a bit like a typical python ORM::

    class Database(Resource):

        username = argument.String()
        password = argument.String()
        port = argument.String()
        ssl = argument.Boolean()

States that you want to target, such as "ensure it exists with these settings"
are implemented as "targets". A target compares the local resource definition
to the remote state and works out a series of changes to apply to bring the API
up to date.

Resources pack as much validation as possible::

    class Foo(Resource):
        some_int = argument.Integer(min=1, max=32)
        some_enum = argument.String(choices=["foo", "bar"])

And foreign-key like inter-resource relationships allow us to track the
dependencies::

    class VPC(Resource):
        name = argument.String()
        <..snip..>

    class Subnet(Resource):
        name = argument.String()
        vpc = argument.Resource(VPC)
        <..snip..>

When you assign a value to the "vpc" parameter of the subnet, you are providing
an implicit dependency hint. These dependency hints allow us to ensure a VPC is
created before a Subnet.


AWS and botocore
----------------

The AWS platform provides a wide variety of components to use. Whilst the API
is not entirely consistent it is consistent enough that we can generically
map touchdown resources to CRUD calls. This means idempotent configuration
management for services for botocore should be straightforward.

An AWS resource implementation might look like this::

    class KeyPair(Resource):
        resource_name = "keypair"

        name = argument.String(field="KeyName")
        public_key = argument.String(field="PublicKeyMaterial")

This maps the touchdown model to the AWS fields ``KeyName`` and
``PublicKeyMaterial``. To actually allow idempotent CRUD for this resource we
use the ``SimpleApply`` mixin::

    class Apply(SimpleApply, Plan):
        resource = KeyPair
        service_name = 'ec2'
        create_action = "import_key_pair"
        describe_action = "describe_key_pairs"
        describe_list_key = "KeyPairs"
        key = 'KeyName'

        def get_describe_filters(self):
            return {"KeyNames": [self.resource.name]}

This is enough for a "ensure it exists" implementation of KeyPairs at Amazon.
For some components you don't even need to overrride
``get_describe_filters``.

If you can't describe an object well enough with filters to return a single
object then you need to override ``describe_object``. For example, for s3::

    def describe_object(self):
        for bucket in self.client.list_buckets()['Buckets']:
            if bucket['Name'] == self.resource.name:
                return bucket

Because the botocore library is quite low level one of the main tasks in
binding the API is mapping touchdown resources to JSON. The
``touchdown.aws.serializers`` library helps here.

In S3 the location field is weirdly in a sub-dictionary. We need to generate JSON that looks like::

    {
        "Bucket": "bucket-name",
        "CreateBucketConfiguration": {
            "LocationConstraint": "eu-west-1",
        }
    }

We can write a resource that handles this with the ``serializer`` annotations::

    class Bucket(Resource):
        resource_name = "bucket"

        name = argument.String(field="Bucket")
        region = argument.String(
            field="CreateBucketConfiguration",
            serializer=serializers.Dict(
                LocationConstraint=serializers.Identity(),
            )
        )
