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

from touchdown.core import argument, errors
from touchdown.core.plan import Plan
from touchdown.core.resource import Resource
from touchdown.core.workspace import Workspace


class LocalFolder(Resource):

    resource_name = 'local_folder'

    name = argument.String()
    root = argument.Resource(Workspace)

    def clean_name(self, name):
        return os.path.abspath(os.path.expanduser(name))


class Describe(Plan):

    resource = LocalFolder
    name = 'describe'

    def get_actions(self):
        if not os.path.isdir(self.resource.name):
            raise errors.NotFound('"{}" could not be found, or is not a folder'.format(self.resource))
        return []
