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

import os

from touchdown.core.resource import Resource
from touchdown.core.plan import Plan
from touchdown.core import argument, errors

from .folder import LocalFolder


class LocalFile(Resource):

    resource_name = "file"

    name = argument.String()
    # path = argument.Computed(lambda r: os.path.join(r.folder.name, r.name))
    folder = argument.Resource(LocalFolder)


class Describe(Plan):

    resource = LocalFile
    name = "describe"

    def get_actions(self):
        if not os.path.isfile(os.path.join(self.resource.folder.name, self.resource.name)):
            raise errors.NotFound("'{}' could not be found, or is not a file".format(self.resource))
        return []

    def read(self):
        return open(self.resource.name, 'r')

    def write(self, contents):
        with open(self.resource.name, 'w') as fp:
            fp.write(contents)
