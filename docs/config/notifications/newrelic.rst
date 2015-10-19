New Relic deployment notifications
==================================


.. class:: NewRelicDeploymentNotification

    You can send a notification from the workspace::

        script = workspace.add_new_relic_deployment_notification(
            apikey="XXXXXXXXXXXXXXXXXXXXXXXX",
            app="myapp-staging",
            revision="3.1.0"
        )

    This uses the `New Relic Deployment Notification REST API <https://docs.newrelic.com/docs/apm/new-relic-apm/maintenance/deployment-notifications#api>`_.

    .. attribute:: apikey

        Your NewRelic API key. This is seperate from your licence key. Required.

    .. attribute:: app

        The name of the application to record the deployment against. Required.

    .. attribute:: revision

        The version of software that was just deployed. Required. Max 127 characters.

    .. attribute:: description

        A description of the change. Max 65535 characters.

    .. attribute:: changelog

        A copy of the changelog to attach to this deployment record. Max 65535 characters.

    .. attribute:: user

        The user that pushed this changed. Max 31 characters.
