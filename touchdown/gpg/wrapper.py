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

from six import StringIO

from touchdown.core.plan import Plan
from touchdown.core import argument
from touchdown.interfaces import File

from .gpg import Gpg


class Wrapper(File):

    resource_name = "cipher"

    name = argument.String()
    file = argument.Resource(File)

    gpg = argument.Resource(Gpg)


class Describe(Plan):

    resource = Wrapper
    name = "describe"

    def get_actions(self):
        return []

    def read(self):
        fp = self.runner.get_plan(self.resource.file)
        gpg = self.runner.get_plan(self.resource.gpg).get_gnupg()
        return StringIO(gpg.decrypt_file(
            fp.read(),
            passphrase=self.resource.gpg.passphrase,
        ))

    def write(self, c):
        fp = self.runner.get_plan(self.resource.file)
        gpg = self.runner.get_plan(self.resource.gpg).get_gnupg()
        fp.write(str(gpg.encrypt(
            c,
            recipients=self.resource.gpg.recipients,
            symmetric=self.resource.gpg.symmetric,
            passphrase=self.resource.gpg.passphrase,
        )))
