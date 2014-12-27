# Copyright 2014 Isotoma Limited
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

from botocore import session

from touchdown.core import errors
from touchdown.core.action import Action


class SetTags(Action):

    def __init__(self, runner, target, resources, tags):
        super(SetTags, self).__init__(runner, target)
        self.resources = resources
        self.tags = tags

    @property
    def description(self):
        yield "Set tags on resource {}".format(self.resource.name)
        for k, v in self.tags.items():
            yield "{} = {}".format(k, v)

    def run(self):
        operation = self.target.service.get_operation("CreateTags")
        response, data = operation.call(
            self.target.endpoint,
            Resources=self.resources,
            Tags=[{"Key": k, "Value": v} for k, v in self.tags.items()],
        )

        if response.status_code != 200:
            raise errors.Error("Failed to update resource tags")


class SimpleApply(object):

    name = "apply"
    default = True

    def __init__(self, *args, **kwargs):
        super(SimpleApply, self).__init__(*args, **kwargs)
        self.session = session.Session()
        # self.session.set_credentials(aws_access_key_id, aws_secret_access_key)
        self.service = self.session.get_service("ec2")
        self.endpoint = self.service.get_endpoint("eu-west-1")

    def get_object(self):
        pass

    def get_actions(self, runner):
        self.object = self.get_object()
        if not self.object:
            yield self.add_action(runner, self)
            return

        if hasattr(self.resource, "tags"):
            tags = dict((v["Key"], v["Value"]) for v in self.object.get('Tags', []))

            if tags.get('name', '') != self.resource.name:
                yield SetTags(
                    runner,
                    self,
                    resources=[self.key],
                    tags={"name": self.resource.name}
                )

    @property
    def resource_id(self):
        return self.object[self.key]
