# Copyright 2016 Isotoma Limited
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

import datetime
import os

from touchdown.core.datetime import utc

from .service import ServiceStubber


class ServerCertificateStubber(ServiceStubber):

    client_service = 'iam'

    # generated according to http://pages.cs.wisc.edu/~zmiller/ca-howto/
    cert_file = os.path.join(os.path.dirname(__file__), '../../assets/host.crt')
    key_file = os.path.join(os.path.dirname(__file__), '../../assets/host.key')
    chain_file = os.path.join(os.path.dirname(__file__), '../../assets/chain.crt')
    bad_chain_file = os.path.join(os.path.dirname(__file__), '../../assets/bad_chain.crt')

    def add_list_server_certificate_empty_response(self):
        self.add_response(
            'list_server_certificates',
            service_response={'ServerCertificateMetadataList': []},
            expected_params={}
        )

    def add_list_server_certificate_one_response(self):
        self.add_response(
            'list_server_certificates',
            service_response={'ServerCertificateMetadataList': [{
                # see touchdown/aws/replacement.py
                'ServerCertificateName': self.resource.name + '.1',
                'ServerCertificateId': self.make_id(self.resource.name),
                'Path': '/',
                'Arn': self.make_id(self.resource.name),
            }]},
            expected_params={}
        )

    def add_upload_server_certificate(self):
        with open(self.cert_file) as cert_file, open(self.key_file) as key_file, open(self.chain_file) as chain_file:
            self.add_response(
                'upload_server_certificate',
                service_response={},
                expected_params={
                    'ServerCertificateName': self.resource.name + '.1',
                    'CertificateBody': cert_file.read(),
                    'PrivateKey': key_file.read(),
                    'CertificateChain': chain_file.read(),
                }
            )

    def add_get_server_certificate(self):
        with open(self.cert_file) as cert_file, open(self.chain_file) as chain_file:
            self.add_response(
                'get_server_certificate',
                service_response={'ServerCertificate': {
                    'ServerCertificateMetadata': {
                        'ServerCertificateName': self.resource.name + '.1',
                        'ServerCertificateId': self.make_id(self.resource.name),
                        'Path': '/',
                        'Arn': self.make_id(self.resource.name),
                        'Expiration': datetime.datetime.utcnow().replace(tzinfo=utc)
                    },
                    'CertificateBody': cert_file.read(),
                    'CertificateChain': chain_file.read(),
                }},
                expected_params={'ServerCertificateName': self.resource.name + '.1'}
            )

    def add_delete_server_certificate(self):
        self.add_response(
            'delete_server_certificate',
            service_response={},
            expected_params={'ServerCertificateName': self.resource.name + '.1'}
        )
