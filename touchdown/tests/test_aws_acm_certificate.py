# Copyright 2015 Isotoma Limited
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

from touchdown.tests.aws import StubberTestCase
from touchdown.tests.stubs.aws import CertificateStubber


class TestCreateCertificate(StubberTestCase):

    def test_create_acm_certificate(self):
        goal = self.create_goal('apply')

        acm_certificate = self.fixtures.enter_context(CertificateStubber(
            goal.get_service(
                self.aws.add_acm_certificate(
                    name='example.com',
                ),
                'apply',
            )
        ))
        acm_certificate.add_list_certificates_empty_response()
        acm_certificate.add_request_certificate()
        acm_certificate.add_describe_certificate()
        acm_certificate.add_list_certificates_empty_response()

        goal.execute()

    def test_create_acm_certificate_idempotent(self):
        goal = self.create_goal('apply')

        acm_certificate = self.fixtures.enter_context(CertificateStubber(
            goal.get_service(
                self.aws.add_acm_certificate(
                    name='example.com',
                ),
                'apply',
            )
        ))
        acm_certificate.add_list_certificates_one_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(acm_certificate.resource)), 0)


class TestDestroyCertificate(StubberTestCase):

    def test_destroy_acm_certificate(self):
        goal = self.create_goal('destroy')

        acm_certificate = self.fixtures.enter_context(CertificateStubber(
            goal.get_service(
                self.aws.add_acm_certificate(
                    name='example.com',
                ),
                'destroy',
            )
        ))
        acm_certificate.add_list_certificates_one_response()
        acm_certificate.add_delete_certificate()

        goal.execute()

    def test_destroy_acm_certificate_idempotent(self):
        goal = self.create_goal('destroy')

        acm_certificate = self.fixtures.enter_context(CertificateStubber(
            goal.get_service(
                self.aws.add_acm_certificate(
                    name='example.com',
                ),
                'destroy',
            )
        ))
        acm_certificate.add_list_certificates_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(acm_certificate.resource)), 0)
