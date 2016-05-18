Framework
=========

Resource modelling
------------------

The core idea behind Touchdown is that you model your infrastructure with
"Resource" objects. These are declarative objects for describing your
infrastructure. Implementation wise they work a bit like a typical python ORM::

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

One common task is converting between the API that touchdown presents (which
aims to be high level with strong checking capabilities) and the API of the
underlying service. For example, in the case of botocore everything maps down
to JSON-like primitives that map closely to the AWS API. The
``touchdown.core.serializers`` library helps here.

An example: In S3 the location field is weirdly in a sub-dictionary. We need to
generate JSON that looks like::

    {
        "Bucket": "bucket-name",
        "CreateBucketConfiguration": {
            "LocationConstraint": "eu-west-1",
        }
    }

We can write a resource that handles this with the ``serializer`` annotation::

    class Bucket(Resource):
        resource_name = "bucket"

        name = argument.String(field="Bucket")
        region = argument.String(
            field="CreateBucketConfiguration",
            serializer=serializers.Dict(
                LocationConstraint=serializers.Identity(),
            )
        )

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
        describe_envelope = "KeyPairs"
        key = 'KeyName'

        def get_describe_filters(self):
            return {"KeyNames": [self.resource.name]}


Finding existing resources at Amazon
------------------------------------

.. class:: SimpleDescribe

    This is a mixin that you use with the ``Plan`` base class. It knows about
    common patterns used at AWS for retrieving metadata about resources already
    created.

    For example::

        class Describe(SimpleDescribe, Plan):

            resource = Bucket
            service_name = 's3'
            describe_action = "list_buckets"
            describe_envelope = "Buckets"
            describe_filters = {}
            describe_object_matches = lambda self, bucket: bucket['Name'] == self.resource.name
            key = 'Bucket'

    .. attribute:: service_name

        This is the name of an API service, for example ``ec2`` or ``sns``. It
        matches the parameter you would pass to botocore's ``create_client()``.

Under the hood finding a resource generally involves calling an API that returns a list of resources. Touchdown will automatically handle pagination where botocore provides a paginator but it needs helping filtering the objects returned:

  * Some listing API's take a name parameter and can return a list of a single matching item.

  * Some take a list of filter predicates and values. These let you filter on everything from the instance size to its state to a tag.

  * Some API's do not support any server side filtering at all. We have to retrieve all ojects and filter then client side.

The following attributes and functions control how the object finding process works.

    .. attribute:: describe_action

        The name of a botocore API. For example ``list_topics`` or ``describe_roles``.

    .. attribute:: describe_filters

        A set of filters to pass to the API. As it is not very useful to pass
        a static set of filters this is generally a property::

            @property
            def describe_filters(self):
                return {"Name": self.resource.name}

    .. method:: get_describe_filters()

        This method is called to build kwargs to pass to botocore. The default
        implementation is::

            def get_describe_filters(self):
                return {
                    self.key: self.resource.name
                }

        This is only useful where the resource type's id is the user specified
        name, such as a :class:`~touchdown.aws.rds.Database` or
        :class:`~touchdown.aws.elasticache.Cache`. For a resource where the id
        is generated by Amazon itself you might need to build a filter list::

            def get_describe_filters(self):
                vpc = self.runner.get_plan(self.resource.vpc)
                if not vpc.resource_id:
                    return None

                if self.key in self.object:
                    return {
                        "Filters": [
                            {'Name': 'route-table-id', 'Values': [self.object[self.key]]}
                        ]
                    }

                return {
                    "Filters": [
                        {'Name': 'tag:Name', 'Values': [self.resource.name]},
                        {'Name': 'vpc-id':, 'Values': vpc.resource_id}
                    ],
                }

        This example also highlights that you can use different filters
        depending on how much data you have collected. After a
        :class:`~touchdown.aws.vpc.RouteTable` has just been created but before
        it has been named the first will work, but the second won't - it doesn't
        have a name until we apply the tags.

        If get_describe_filters returns ``None`` it signals that the resource
        can't exist yet. In this case, if a :class:`~touchdown.aws.vpc.VPC`
        doesn't have a resource_id then it can't exist, and as the
        ``RouteTable`` must be in a ``VPC`` it can't exist either.

    .. attribute:: describe_object_matches

        A callable that does client side filtering of a list of Amazon resources.
        It is called for each item retrieved and passed the parsed JSON. It
        should return ``True`` if it matches the current resource.

        For example::

            def describe_object_matches(self, data):
                return data['Name'] == self.resource.name

        This is much less efficient than passing a filter to the API, but not
        all AWS API's have advanced enough filtering.

    .. attribute:: describe_notfound_exception

        Some API's will return an empty list when there are no matching results. However some will return an error that manifests as a botocore ``ClientError`` exception. If the error type matches ``describe_notfound_exception`` then it will be captured and treated like the API return no matches.


The data returned by the API may need some massaging before it is useful.

    .. attribute:: describe_envelope

        The envelope that the response is wrapped in. This is a jmespath
        expression. For example, a CloudFront Distribution will return data like
        this::

            {
                "DistributionList": {
                    "Items": [
                        "Id": "ABZDEFG",
                        "DomainName": "www.example.com",
                        ...
                    ]
                }
            }

        So the expression is ``DistributionList.Items``.

        If you need to use an API that returns a single item rather than a list of items you can use jmespath here too. For example, in SQS we use `get_queue_url` instead of a listing API:

            describe_action = 'get_queue_url'
            describe_envelope = "[@]"

    .. attribute:: key

        This is the field in the result that contains that object id. For
        example, ``SecurityGroupId`` or ``SubnetId``.

        This field is how `serializers.Identifier()` determines the unique id for a resource: It simply looks up the `key` in the description of the resource that was retrieved.

    .. method:: annotate_object

        Some list API's do not return enough information to be usable by touchdown. We have to extend that information by calling an additional API. `annotate_object()` is a hook that is called on the output of the describe step so that subclasses can add this additional information.

        For example, `WAF` does not return much information from its `list_rules` API so in order to get the predicates for that rule we need to annotate the results::

            def annotate_object(self, rule):
                result = self.client.get_rule(
                    RuleId=self.object['RuleId'],
                )
                rule.update(result['Rule'])
                return rule


Creating new instances
----------------------

Before creating a new instance we have to check if an instance exists already.
We leverage the ``SimpleDescribe`` subclass we have already made to do this,
and mix in the ``SimpleApply`` mixin to create an instance if its missing (and
apply any required changes).


.. class:: SimpleApply

    For example::

        class Apply(SimpleApply, Describe):

            create_action = "import_key_pair"
            create_response = "id-only"

    .. attribute:: create_action

        A botocore API that can be used to create an instance.

    .. attribute:: create_response

        The results from the various Amazon API's vary, but fit into a handful
        of common patterns:

        ``full-description``
            The result of this API is a description complete enough that we
            don't need to call the describe API again.
        ``id-only``
            The response contains the ID of the newly created resource, but
            it does not contain the full data you would get if you called the
            describe API.
        ``not-that-useful``
            Beyond reporting success via a HTTP ``200``, the API has no outputs.

        If not specified, ``full-description`` is assumed.

    .. attribute:: create_envelope

        A jmespath expresion for extracting the metadata from a create API call.
        This is generally just the name of an object - like ``Bucket`` or
        ``Topic``. By default this drops the last charcter from
        ``describe_envelope``.

    .. method:: get_create_serializer()

        Returns a serializer instance that can turn the resource into kwargs
        that are passed to botocore.

        The default implementation is::

            def get_create_serializer(self):
                return serializers.Resource()

        This uses the ``field`` and ``serializer`` annotations automatically
        so in most cases does not need customizing when adding a new resource
        type.

    .. method:: update_object()

        This method is called to update an existing or newly created object.
        It should cope with the fact that self.object might not be set yet (which
        would indicate a newly created object).

        It should yield actions that can be executed later. As there are very
        few recurring patterns for updating instances at AWS, the implementation
        is quite specific to the service.


Destroying instances
--------------------

.. class:: SimpleDestroy

    This is a mixin to create a ``destroy`` plan for a resource. It should be
    mixed with a concrete subclass of :class:`SimpleDescribe`.

    For example::

        class Destroy(SimpleDestroy, Describe):
            destroy_action = "delete_security_group"

    .. attribute:: destroy_action

        The botocore API to call to delete an instance.

    .. method:: get_destroy_serializer()

        Returns a serializer instance that can turn the resource into kwargs
        that are passed to botocore.

        The default implementation is::

            def get_destroy_serializer(self):
                return serializers.Dict(**{self.key: self.resource_id})

        In most cases this will correctly pass the ID of the resource to be
        deleted to botocore, so it often doesn't need implementing for new
        subclasses.
