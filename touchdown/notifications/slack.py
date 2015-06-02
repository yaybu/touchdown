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

from touchdown.core import argument, action, errors, plan, resource, serializers, workspace


class SlackNotification(resource.Resource):

    resource_name = "slack_notification"

    webhook = argument.String()
    username = argument.String(default="yaybu", field="username")
    channel = argument.String(field="channel")
    icon_url = argument.String(default="https://avatars3.githubusercontent.com/u/5338681", field="icon_url")
    icon_emoji = argument.String(field="icon_emoji")
    text = argument.String(field="text")

    root = argument.Resource(workspace.Workspace)


class SlackNotificationAction(action.Action):

    @property
    def description(self):
        yield "Post slack notification to {}".format(self.resource.channel)

    def run(self):
        response = requests.post(
            self.resource.webhook,
            data=serializers.Json(serializers.Resource()).render(self.runner, self.resource)
        )
        if response.status_code != 200:
            raise errors.Error("Error submitting notification: {}".format(response.text))


class Apply(plan.Plan):

    name = "apply"
    resource = SlackNotification

    def get_actions(self):
        yield SlackNotificationAction(self)
