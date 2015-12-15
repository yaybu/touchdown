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

    .. attribute:: parent

        The resource this resource is attached to::

            dog = rest_api.add_resource(
                name='/animal/dog',
                parent=animal,
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
