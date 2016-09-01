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

from touchdown.core import argument
from touchdown.core.plan import Plan
from touchdown.interfaces import File, FileNotFound

from .folder import LocalFolder


class LocalFile(File):

    resource_name = 'file'

    name = argument.String()
    path = argument.Callable(lambda r: os.path.join(r.folder.name, r.name))
    folder = argument.Resource(LocalFolder)


class FileIo(Plan):

    resource = LocalFile
    name = 'fileio'

    def read(self):
        try:
            return open(self.resource.path, 'rb')
        except IOError:
            raise FileNotFound(self.resource.path)

    def write(self, contents):
        with open(self.resource.path, 'wb') as fp:
            fp.write(contents)
