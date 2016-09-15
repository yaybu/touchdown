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

import binascii
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import asymmetric, serialization
from cryptography.x509 import load_pem_x509_certificate
from cryptography.x509.oid import ExtensionOID, NameOID

from touchdown.core import argument, datetime, errors
from touchdown.core.plan import Plan
from touchdown.core.resource import Resource
from touchdown.core.utils import force_bytes

from ..account import BaseAccount
from ..replacement import (
    ReplacementApply,
    ReplacementDescribe,
    ReplacementDestroy,
)


def split_cert_chain(chain):
    lines = []
    for line in chain.split('\n'):
        if not line:
            continue
        lines.append(line)
        if line == '-----END CERTIFICATE-----':
            yield '\n'.join(lines).encode('utf-8')
            lines = []
    if lines:
        yield '\n'.join(lines).encode('utf-8')


def format_key_identifier(hex):
    hex = str(binascii.hexlify(hex))
    return ':'.join([hex[i:i+2] for i in range(0, len(hex), 2)])


class ServerCertificate(Resource):

    resource_name = 'server_certificate'
    field_order = [
        'private_key',
        'certificate_body',
        'certificate_chain',
    ]

    name = argument.String(field='ServerCertificateName', update=False)
    path = argument.String(field='Path')
    private_key = argument.String(field='PrivateKey', secret=True, update=False)
    certificate_body = argument.String(field='CertificateBody')
    certificate_chain = argument.String(field='CertificateChain')

    account = argument.Resource(BaseAccount)

    def clean_certificate_body(self, value):
        backend = default_backend()
        cert = load_pem_x509_certificate(force_bytes(value), backend)
        private_key = serialization.load_pem_private_key(
            self.private_key.encode('utf-8'),
            password=None,
            backend=backend,
        )

        if cert.public_key().public_numbers() != private_key.public_key().public_numbers():
            raise errors.Error(
                'Certificate does not match private_key',
            )

        return value.strip()

    def clean_certificate_chain(self, value):
        # Perform a basic validation of the SSL chain.
        # This isn't a complete and secure validation. It's just to try and
        # catch problems before doing a deployment.
        backend = default_backend()

        certs = [load_pem_x509_certificate(force_bytes(self.certificate_body), backend)]
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
                error_message = '\n'.join([
                    'Invalid chain for  {} at position {}.',
                    'Expected cert with subject "{}" and subject key identifier "{}".',
                    'Got cert with subject "{}" and subject key identifier "{}".',
                ])
                cert_name = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
                cert_issuer = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
                akib = cert.extensions.get_extension_for_oid(ExtensionOID.AUTHORITY_KEY_IDENTIFIER).value.key_identifier
                aki = format_key_identifier(akib)
                issuer_name = issuer.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
                skib = issuer.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_KEY_IDENTIFIER).value.digest
                ski = format_key_identifier(skib)
                raise errors.Error(
                    error_message.format(
                        cert_name,
                        i,
                        cert_issuer,
                        aki,
                        issuer_name,
                        ski,
                    ))

        return value.strip()


class Describe(ReplacementDescribe, Plan):

    resource = ServerCertificate
    service_name = 'iam'
    api_version = '2010-05-08'
    describe_action = 'list_server_certificates'
    describe_envelope = 'ServerCertificateMetadataList'
    describe_filters = {}
    key = 'ServerCertificateName'
    biggest_serial = 0

    def get_possible_objects(self):
        for obj in super(Describe, self).get_possible_objects():
            response = self.client.get_server_certificate(
                ServerCertificateName=self.name_for_remote(obj),
            )['ServerCertificate']

            result = dict(response['ServerCertificateMetadata'])
            result['CertificateBody'] = response['CertificateBody']
            result['CertificateChain'] = response['CertificateChain']

            yield result


class Apply(ReplacementApply, Describe):

    create_action = 'upload_server_certificate'
    create_response = 'not-that-useful'
    destroy_action = 'delete_server_certificate'

    def is_stale(self, server_certificate):
        if server_certificate['Expiration'] >= datetime.now():
            # Don't delete valid certificates
            return False
        return super(Apply, self).is_stale(server_certificate)


class Destroy(ReplacementDestroy, Describe):

    destroy_action = 'delete_server_certificate'
