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

from .service import ServiceStubber


class CertificateStubber(ServiceStubber):

    client_service = 'acm'

    def add_list_certificates_empty_response(self):
        self.add_response(
            'list_certificates',
            service_response={},
            expected_params={}
        )

    def add_list_certificates_one_response(self):
        self.add_response(
            'list_certificates',
            service_response={'CertificateSummaryList': [
                {'CertificateArn': self.make_id(self.resource.name),
                 'DomainName': self.resource.name}
            ]},
            expected_params={}
        )

    def add_delete_certificate(self):
        self.add_response(
            'delete_certificate',
            service_response={},
            expected_params={'CertificateArn': self.make_id(self.resource.name)}
        )

    def add_request_certificate(self):
        self.add_response(
            'request_certificate',
            service_response={'CertificateArn': self.make_id(self.resource.name)},
            expected_params={'DomainName': self.resource.name}
        )

    def add_describe_certificate(self):
        self.add_response(
            'describe_certificate',
            service_response={'Certificate': {'Status': 'ISSUED'}},
            expected_params={'CertificateArn': self.make_id(self.resource.name)}
        )
