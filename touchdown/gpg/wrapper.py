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

from six import BytesIO

from touchdown.core import argument
from touchdown.core.plan import Plan
from touchdown.core.utils import force_bytes
from touchdown.interfaces import File

from .gpg import Gpg


class Wrapper(File):

    resource_name = 'cipher'

    name = argument.String()
    file = argument.Resource(File)

    gpg = argument.Resource(Gpg)


class FileIo(Plan):

    resource = Wrapper
    name = 'fileio'

    def read(self):
        fp = self.runner.get_service(self.resource.file, 'fileio')
        gpg = self.runner.get_service(self.resource.gpg, 'describe').get_gnupg()
        result = force_bytes(str(gpg.decrypt(
            force_bytes(fp.read().read()),
            passphrase=self.resource.gpg.passphrase,
        )))
        return BytesIO(result)

    def write(self, c):
        fp = self.runner.get_service(self.resource.file, 'fileio')
        gpg = self.runner.get_service(self.resource.gpg, 'describe').get_gnupg()
        fp.write(force_bytes(str(gpg.encrypt(
            force_bytes(c),
            recipients=self.resource.gpg.recipients,
            symmetric=self.resource.gpg.symmetric,
            passphrase=self.resource.gpg.passphrase,
        ))))
