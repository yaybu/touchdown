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

from touchdown.core import argument, resource, serializers

from .local import Local


class LocalOutput(resource.Resource):

    resource_name = "local_output"

    name = argument.String()

    local = argument.Resource(Local)


class LocalOutputAsString(serializers.Serializer):

    def __init__(self, resource):
        self.resource = resource

    def render(self, runner, object):
        with open(self.resource.name) as fp:
            return fp.read()

    def dependencies(self, object):
        return frozenset((self.resource, ))


argument.String.register_adapter(LocalOutput, lambda r: LocalOutputAsString(r))
