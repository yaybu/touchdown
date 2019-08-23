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

from touchdown.core import argument, errors
from touchdown.core.resource import Resource


class Adapter(Resource):

    adapts = argument.Resource(Resource)
    input = None

    def get_serializer(self, runner):
        raise NotImplementedError(self.get_serializer)

    @classmethod
    def wrap(cls, parent, resource):
        for adapter in cls.__subclasses__():
            if adapter.input and isinstance(resource, adapter.input):
                return adapter(parent, adapts=resource)
        raise errors.Error("Cannot turn {} into a {}".format(resource, cls))
