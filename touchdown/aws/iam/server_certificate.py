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

from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import asymmetric

from touchdown.core.resource import Resource
from touchdown.core.plan import Plan
from touchdown.core import argument, errors

from ..account import BaseAccount
from ..common import SimpleDescribe, SimpleApply, SimpleDestroy


def split_cert_chain(chain):
    lines = []
    for line in chain.split("\n"):
        if not line:
            continue
        lines.append(line)
        if line == "-----END CERTIFICATE-----":
            yield "\n".join(lines).encode("utf-8")
            lines = []
    if lines:
        yield "\n".join(lines).encode("utf-8")


class ServerCertificate(Resource):

    resource_name = "server_certificate"
    field_order = [
        "certificate_body",
        "certificate_chain",
    ]

    name = argument.String(field="ServerCertificateName")
    path = argument.String(field='Path')
    certificate_body = argument.String(field="CertificateBody")
    private_key = argument.String(field="PrivateKey", secret=True)
    certificate_chain = argument.String(field="CertificateChain")

    account = argument.Resource(BaseAccount)

    def clean_certificate_chain(self, value):
        # Perform a basic validation of the SSL chain.
        # This isn't a complete and secure validation. It's just to try and
        # catch problems before doing a deployment.
        backend = default_backend()

        certs = [load_pem_x509_certificate(self.certificate_body, backend)]
        for cert in split_cert_chain(value):
            certs.append(load_pem_x509_certificate(cert, backend))

        for i, (cert, issuer) in enumerate(zip(certs, certs[1:])):
            verifier = issuer.public_key().verifier(
                cert.signature,
                asymmetric.padding.PKCS1v15(),
                cert.signature_hash_algorithm,
            )
            verifier.update(cert.tbs_certificate_bytes)
            try:
                verifier.verify()
            except:
                raise errors.Error(
                    "Invalid chain: {} (issued by {}) -> {}. At position {}.".format(
                        cert.subject,
                        cert.issuer,
                        issuer.subject,
                        i
                    ))

        return value


class Describe(SimpleDescribe, Plan):

    resource = ServerCertificate
    service_name = 'iam'
    describe_action = "get_server_certificate"
    describe_envelope = "ServerCertificate"
    describe_notfound_exception = "NoSuchEntity"
    key = 'ServerCertificateName'

    def describe_object(self):
        object = super(Describe, self).describe_object()
        if object:
            result = dict(object['ServerCertificateMetadata'])
            result['CertificateBody'] = object['CertificateBody']
            result['CertificateChain'] = object['CertificateChain']
            return result


class Apply(SimpleApply, Describe):

    create_action = "upload_server_certificate"
    create_response = "not-that-useful"


class Destroy(SimpleDestroy, Describe):

    destroy_action = "delete_server_certificate"
