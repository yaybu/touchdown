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

import os

from botocore import session

from touchdown.core.resource import Resource
from touchdown.core.plan import Plan
from touchdown.core import argument

from touchdown.core.workspace import Workspace


class BaseAccount(Resource):

    dot_ignore = True

    region = argument.String()
    access_key_id = argument.String()
    secret_access_key = argument.String()


class Account(BaseAccount):

    resource_name = "aws"

    root = argument.Resource(Workspace)


class Describe(Plan):

    resource = Account
    default = True
    name = "describe"
    _session = None

    @property
    def session(self):
        if not self._session:
            data_path = os.path.join(os.path.dirname(__file__), "data")
            self._session = session.get_session({
                "data_path": ('data_path', 'BOTO_DATA_PATH', data_path),
            })
            self._session.access_key_id = self.resource.access_key_id or None
            self._session.secret_access_key = self.resource.secret_access_key or None
            self._session.session_token = None
            self._session.region = self.resource.region

        return self._session
