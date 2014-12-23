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

from touchdown.core.action import Action


class SetTags(Action):

    def __init__(self, policy, resources, tags):
        super(SetTags, self).__init__(policy)
        self.resources = resources
        self.tags = tags

    @property
    def description(self):
        yield "Set tags on resource {}".format(self.resource.name)
        for k, v in self.tags.items():
            yield "{} = {}".format(k, v)

    def run(self):
        operation = self.policy.service.get_operation("CreateTags")
        response, data = operation.call(
            self.policy.endpoint,
            Resources=self.resources,
            Tags=[{"Key": k, "Value": v} for k, v in self.tags.items()],
        )

        if response.status_code != 200:
            raise errors.Error("Failed to update hosted zone comment")
