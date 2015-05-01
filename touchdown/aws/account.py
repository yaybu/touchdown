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

from touchdown.core.resource import Resource
from touchdown.core.plan import Plan
from touchdown.core import argument

from touchdown.core.workspace import Workspace

from .session import Session


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
            self._session = Session(
                access_key_id=self.resource.access_key_id or None,
                secret_access_key=self.resource.secret_access_key or None,
                session_token=None,
                expiration=None,
                region=self.resource.region,
            )
        return self._session

    # def get_actions(self):
    #     response = self.session.create_client("iam").get_user()
    #     if not "User" in response:
    #         raise error.Error("Unable to call GetUser on self")
    #     self.object = {
    #         "AccountNumber": response["User"]["Arn"].split(":")[4]
    #     }
    #     return []
