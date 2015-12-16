Creating an Amazon API Gateway for domain redirect
==================================================

Eric Hammond published a `blog post <https://alestic.com/2015/11/amazon-api-gateway-aws-cli-redirect/>`_ about getting started with API Gateway. He built a simple gateway that could redirect a vanity domain name. In this walkthrough we'll replicate that setup with Touchdown.

In the blog post there are some variables - lets replicate them::

    base_domain = 'erichammond.xyz'
    target_url = 'https://twitter.com/esh'

    api_name = base_domain
    api_description = "Redirect $base_domain to $target_url"
    resource_path = "/"
    stage_name = "prod"
    region = "us-east-1"

    certificate_name = base_domain
    certificate_body = base_domain + ".crt"
    certificate_private_key = base_domain + ".key"
    certificate_chain = base_domain + "-chain.crt"

As it's an AWS example we need to setup an AWS workspace::

    aws = workspace.add_aws(
        access_key_id='AKI.....A',
        secret_access_key='dfsdfsdgrtjhwluy52i3u5ywjedhfkjshdlfjhlkwjhdf',
        region='eu-west-1',
    )

    api = aws.add_rest_api(
        name=api_name,
        description=api_description,
    )

    root = api.get_resource(name='/')

    root.add_method(
        method="GET",
        authorization_type = "NONE",
        api_key_required=False,
    )

    root.add_method_response(
        method="GET",
        status_code=301,
        response_models={"application/json": "Empty"},
        response_parameters={"method.response.header.Location": True},
    )

    root.add_integration(
        method="GET",
        type="MOCK",
        request_templates={
            "application/json": "{\"statusCode\": 301}",
        }
    )

    root.add_integration_response(
        method="GET",
        status_code=301,
        response_templates='{"application/json":" redirect"}',
        response_parameters={
            "method.response.header.Location": "'"'$target_url'"'",
        },
    )


Deploying the API
----------------

::
    deployment = api.add_deployment(
        name=base_domain,
        stage_name=stage_name,
        stage_description=stage_name,
    )
    stage = deployment.get_stage(name=stage_name)


Linking to a domain name
========================

::
    stage.add_domain(aws.add_apigateway_domain(
        domain=base_domain,
        certificate_name=certificate_name,
        certificate_body=ceritificate_body,
        certifcate_private_key=certifificate_private_key,
        certificate_chain=certificate_chain,
    ))
