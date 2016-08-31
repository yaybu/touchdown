# Copyright 2015 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import requests

from touchdown.core import (
    action,
    argument,
    errors,
    plan,
    resource,
    serializers,
    workspace,
)


class NewRelicDeploymentNotification(resource.Resource):

    resource_name = 'newrelic_deployment_notification'

    apikey = argument.String()
    name = argument.String(field='deployment[app_name]')
    application_id = argument.String(field='deployment[application_id]')
    description = argument.String(field='deployment[description]')
    changelog = argument.String(field='deployment[changelog]')
    user = argument.String(field='deployment[user]')
    revision = argument.String(field='deployment[revision]')

    root = argument.Resource(workspace.Workspace)


class NotificationAction(action.Action):

    @property
    def description(self):
        yield 'Post deployment notification to NewRelic app {}'.format(self.resource.name)

    def run(self):
        data = serializers.Resource().render(self.runner, self.resource)
        headers = {
            'X-API-Key': self.resource.apikey,
        }
        response = requests.post(
            'https://api.newrelic.com/deployments.xml',
            data=data,
            headers=headers,
        )
        if response.status_code != 201:
            raise errors.Error('Error submitting notification: {}'.format(response.text))


class Apply(plan.Plan):

    name = 'apply'
    resource = NewRelicDeploymentNotification

    signature = (
        plan.Present('name'),
        plan.Present('revision'),
        plan.Present('apikey'),
    )

    def get_actions(self):
        yield NotificationAction(self)
