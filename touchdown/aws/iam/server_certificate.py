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

from ..account import Account
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy


class ServerCertificate(Resource):

    resource_name = "server_certificate"

    name = argument.String(field="ServerCertificateName")
    path = argument.String(field='Path')
    certificate_body = argument.String(field="CertificateBody")
    private_key = argument.String(field="PrivateKey", secret=True)
    certificate_chain = argument.String(field="CertificateChain")

    account = argument.Resource(Account)


class Describe(SimpleDescribe, Plan):

    resource = ServerCertificate
    service_name = 'iam'
    get_action = "get_server_certificate"
    get_key = "ServerCertificate"
    get_notfound_exception = "NoSuchEntity"
    key = 'ServerCertificateName'

    def describe_object(self):
        object = super(Describe, self).describe_object()
        if not object:
            return object
        result = dict(object['ServerCertificateMetadata'])
        result['CertificateBody'] = object['CertificateBody']
        result['CertificateChain'] = object['CertificateChain']
        return result


class Apply(SimpleApply, Describe):

    create_action = "upload_server_certificate"
    create_response = "not-that-useful"


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_server_certificate"
