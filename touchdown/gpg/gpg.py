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

from touchdown.core import argument, errors, workspace
from touchdown.core.plan import Plan
from touchdown.core.resource import Resource

try:
    import gnupg
except ImportError:
    gnupg = None


class Gpg(Resource):

    resource_name = 'gpg'

    name = argument.String()

    home = argument.String()
    keyring = argument.String()
    secret_keyring = argument.String()
    use_agent = argument.Boolean(default=True)
    options = argument.List(argument.String())

    armor = argument.Boolean()
    symmetric = argument.Boolean()
    passphrase = argument.String()
    always_trust = argument.Boolean()
    recipients = argument.List(argument.String())

    root = argument.Resource(workspace.Workspace)


class Describe(Plan):

    resource = Gpg
    name = 'describe'

    def get_gnupg(self):
        return gnupg.GPG()

    def get_actions(self):
        if not gnupg:
            raise errors.NotFound('\'gnupg\' python module is not available.')
        return []
