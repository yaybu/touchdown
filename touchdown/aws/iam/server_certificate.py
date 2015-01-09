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
from touchdown.core.target import Target
from touchdown.core import argument

from ..account import AWS
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy


class ServerCertificate(Resource):

    resource_name = "server_certificate"

    name = argument.String(aws_field="ServerCertificateName")
    path = argument.String(aws_field='Path')
    certificate_body = argument.String(aws_field="CertificateBody")
    private_key = argument.String(aws_field="PrivateKey", secret=True)
    certificate_chain = argument.String(aws_field="CertificateChain")

    account = argument.Resource(AWS)


class Describe(SimpleDescribe, Target):

    resource = ServerCertificate
    service_name = 'iam'
    get_action = "get_server_certificate"
    key = 'ServerCertificateName'


class Apply(SimpleApply, Describe):

    create_action = "upload_server_certificate"


class Destroy(SimpleDestroy, Describe):

    destroy_action = "destroy_server_certificate"
