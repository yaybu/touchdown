API Gateway
===========

.. module:: touchdown.aws.apigateway
   :synopsis: Building serverless API's


Amazon API Gateway is a fully managed service that makes it easy for developers to create, publish, maintain, monitor, and secure APIs at any scale. With a few clicks in the AWS Management Console, you can create an API that acts as a “front door” for applications to access data, business logic, or functionality from your back-end services, such as workloads running on Amazon Elastic Compute Cloud (Amazon EC2), code running on AWS Lambda, or any Web application. Amazon API Gateway handles all the tasks involved in accepting and processing up to hundreds of thousands of concurrent API calls, including traffic management, authorization and access control, monitoring, and API version management. Amazon API Gateway has no minimum fees or startup costs. You pay only for the API calls you receive and the amount of data transferred out.


Setting up a REST API
---------------------

.. class:: RestApi

    To start building an API you need to create a REST API component::

        rest_api = aws.add_rest_api(
            name='my-api',
            description='....',
        )

    .. attribute:: name

        A name for this API.

    .. attribute:: description

        A description for this API.



Defining resources
------------------

.. class:: Resource

    .. attribute:: name

        The name of the resource. This is a uri, for example ``/animal``.

        There will be an implict ``/`` resource created, which you can attach other resources to::

            resource = rest_api.get_resource(name='/')
            animal = resource.add_resource(
                name='/animal',
            )

    .. attribute:: parent_resource

        The resource this resource is attached to::

            dog = rest_api.add_resource(
                name='/animal/dog',
                parent_resource=animal,
            )

        This is optional if you attach a resource directly::

            dog = animal.add_resource(name='/animal/dog')


Defining models
---------------

.. class:: Model

    ::

        rest_api.add_model(
            name='dog',
            description='dog schema',
            schema='',
            content_type='application/json',
        )

    .. attribute:: name

    .. attribute:: description

    .. attribute:: schema

    .. attribute:: content_type

        This defaults to ``application/json``.


Defining deployments
--------------------

.. class:: Deployment

    ::

        rest_api.add_deployment(
            name='api-deployment',
            stage='production',
        )

    .. attribute:: name

    .. attribute:: stage

    .. attribute:: stage_description

    .. attribute:: cache_cluster_enabled

    .. attribute:: cache_cluster_size

    .. attribute:: variables


Adding stages
-------------

A stage defines the path through which an API deployment is accessible. With deployment stages, you can have multiple releases for each API, such as alpha, beta, and production. Using stage variables you can configure an API deployment stage to interact with different backend endpoints.

.. class:: Stage

    You attach new stages to a deployment::

        my_stage = deployment.add_stage(
            name='staging',
        )

    .. attribute:: name

    .. attribute:: description

    .. attribute:: cache_cluster_enabled

    .. attribute:: cache_cluster_size

    .. attribute:: variables


Attaching methods
-----------------

.. class:: Method

    You attach an method to a resource::

        my_method = resource.add_method(
            method = "GET",
        )

    .. attribute:: name

    .. attribute:: authorization_type

    .. attribute:: api_key_required

    .. attribute:: request_parameters

    .. attribute:: request_models


Attaching method responses
--------------------------

.. class:: MethodResponse

    You attach an method response to a resource::

        my_method_response = resource.add_method_response(
            name = "GET",
        )

    .. attribute:: name

    .. attribute:: status_code

    .. attribute:: response_parameters

    .. attribute:: response_models


Attaching integrations
----------------------

.. class:: Integration

    You attach an integration to a resource::

        my_integration = resource.add_integration(
            name = "GET",
        )

    .. attribute:: name

        E.g. ``GET``

    .. attribute:: integration_type

        Can be `HTTP`, `AWS` or `MOCK`.

    .. attribute:: integration_http_method

    .. attribute:: request_parameters

    .. attribute:: request_templates

    .. attribute:: uri

    .. attribute:: credentials

    .. attribute:: cache_namespace

    .. attribute:: cache_key_parameters


Attaching integration responses
-------------------------------

.. class:: IntegrationResponse

    You attach an integration response to a resource::

        my_integration_response = resource.add_integration_response(
            name = "GET",
        )

    .. attribute:: name

        E.g. ``GET``

    .. attribute:: status_code

    .. attribute:: selection_pattern

    .. attribute:: response_parameters

    .. attribute:: response_templates
