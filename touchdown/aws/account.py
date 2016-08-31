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

from threading import Lock

from touchdown.core import argument
from touchdown.core.datetime import now
from touchdown.core.plan import Plan
from touchdown.core.resource import Resource
from touchdown.core.utils import cached_property
from touchdown.core.workspace import Workspace

from .session import Session


class BaseAccount(Resource):

    dot_ignore = True

    region = argument.String()
    access_key_id = argument.String()
    secret_access_key = argument.String()
    mfa_serial = argument.String(field='SerialNumber')


class Account(BaseAccount):

    resource_name = 'aws'

    root = argument.Resource(Workspace)


class Null(Plan):

    resource = Account
    default = True
    name = 'null'
    _session = None

    _acquire_session = Lock()

    @cached_property
    def base_session(self):
        return Session(
            access_key_id=self.resource.access_key_id or None,
            secret_access_key=self.resource.secret_access_key or None,
            session_token=None,
            expiration=None,
            region=self.resource.region,
        )

    @cached_property
    def base_client(self):
        return self.base_session.create_client('sts')

    @property
    def session(self):
        with self._acquire_session:
            if not self._session:
                session = None

                if self.resource.mfa_serial:
                    cache_key = '_'.join((self.resource.access_key_id, self.resource.mfa_serial))
                    if cache_key in self.cache:
                        session = Session.fromjson(self.cache[cache_key])

                    if not session or session.expiration <= now():
                        creds = self.base_client.get_session_token(
                            SerialNumber=self.resource.mfa_serial,
                            TokenCode=self.ui.prompt(
                                'Please enter a token for MFA device {}'.format(self.resource.mfa_serial),
                                key=self.resource.mfa_serial,
                            ),
                        )['Credentials']
                        session = Session(
                            access_key_id=creds['AccessKeyId'],
                            secret_access_key=creds['SecretAccessKey'],
                            session_token=creds['SessionToken'],
                            expiration=creds['Expiration'],
                            region=self.resource.region,
                        )
                        self.cache[cache_key] = session.tojson()
                else:
                    session = self.base_session

                self._session = session
                self._session.region = self.resource.region

        return self._session

    # def get_actions(self):
    #     response = self.session.create_client('iam').get_user()
    #     if not 'User' in response:
    #         raise error.Error('Unable to call GetUser on self')
    #     self.object = {
    #         'AccountNumber': response['User']['Arn'].split(':')[4]
    #     }
    #     return []
