# Copyright 2016 John Carr
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

import ssl

from pyVim.connect import SmartConnect

from touchdown.core import argument
from touchdown.core.plan import Plan
from touchdown.core.resource import Resource
from touchdown.core.utils import cached_property
from touchdown.core.workspace import Workspace


class Connection(Resource):
    resource_name = 'vsphere'
    dot_ignore = True

    host = argument.String(field='host')
    user = argument.String(field='user')
    password = argument.String(field='pwd')
    port = argument.Integer(field='port', default=443)

    root = argument.Resource(Workspace)


class ConnectionPlan(Plan):

    resource = Connection
    name = 'connection'

    @cached_property
    def instance(self):
        sslcontext = None
        if hasattr(ssl, '_create_unverified_context'):
            sslcontext = ssl._create_unverified_context()

        return SmartConnect(
            host=self.resource.host,
            user=self.resource.user,
            pwd=self.resource.password,
            port=self.resource.port,
            sslContext=sslcontext,
        )

    @cached_property
    def content(self):
        return self.instance.RetrieveContent()
