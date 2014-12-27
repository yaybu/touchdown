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

    def __init__(self, runner, target, tags):
        super(SetTags, self).__init__(runner, target)
        self.tags = tags

    @property
    def description(self):
        yield "Set tags on resource {}".format(self.resource.name)
        for k, v in self.tags.items():
            yield "{} = {}".format(k, v)

    def run(self):
        self.target.client.create_tags(
            Resources=[self.target.resource_id],
            Tags=[{"Key": k, "Value": v} for k, v in self.tags.items()],
        )


class SimpleApply(object):

    name = "apply"
    default = True

    def get_object(self, runner):
        pass

    def get_actions(self, runner):
        self.object = self.get_object(runner)

        if not self.object:
            self.object = {}
            yield self.add_action(runner, self)

        if hasattr(self.resource, "tags"):
            local_tags = dict(self.resource.tags)
            local_tags['name'] = self.resource.name

            remote_tags = dict((v["Key"], v["Value"]) for v in self.object.get('Tags', []))

            tags = {}
            for k, v in local_tags.items():
                if k not in remote_tags or remote_tags[k] != v:
                    tags[k] = v

            if tags:
                yield SetTags(
                    runner,
                    self,
                    tags={"name": self.resource.name}
                )

    @property
    def resource_id(self):
        return self.object[self.key]
