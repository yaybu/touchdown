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

from touchdown.core import errors
from touchdown.tests.aws import StubberTestCase
from touchdown.tests.stubs.aws import ServerCertificateStubber


class TestCreateServerCertificate(StubberTestCase):

    def test_create_server_certificate(self):
        goal = self.create_goal('apply')

        with open(ServerCertificateStubber.cert_file) as cert_file,\
                open(ServerCertificateStubber.key_file) as key_file,\
                open(ServerCertificateStubber.chain_file) as chain_file:
            server_certificate = self.fixtures.enter_context(ServerCertificateStubber(
                goal.get_service(
                    self.aws.add_server_certificate(
                        name='my-test-server-certificate',
                        certificate_body=cert_file.read(),
                        private_key=key_file.read(),
                        certificate_chain=chain_file.read(),
                    ),
                    'apply',
                )
            ))
        # first list is to find things to delete
        server_certificate.add_list_server_certificate_empty_response()
        # second is to find if there is an existing matching cert
        server_certificate.add_list_server_certificate_empty_response()
        server_certificate.add_upload_server_certificate()
        # CreateAction needs to look up cert again as create response has no info
        server_certificate.add_list_server_certificate_one_response()
        server_certificate.add_get_server_certificate()
        # refresh resource metadata
        server_certificate.add_list_server_certificate_one_response()
        server_certificate.add_get_server_certificate()
        # sanity check / PostCreation
        server_certificate.add_list_server_certificate_one_response()
        server_certificate.add_get_server_certificate()

        goal.execute()

    def test_create_server_certificate_idempotent(self):
        goal = self.create_goal('apply')

        with open(ServerCertificateStubber.cert_file) as cert_file, open(ServerCertificateStubber.key_file) as key_file:
            server_certificate = self.fixtures.enter_context(ServerCertificateStubber(
                goal.get_service(
                    self.aws.add_server_certificate(
                        name='my-test-server-certificate',
                        certificate_body=cert_file.read(),
                        private_key=key_file.read()
                    ),
                    'apply',
                )
            ))
        server_certificate.add_list_server_certificate_one_response()
        server_certificate.add_get_server_certificate()
        server_certificate.add_list_server_certificate_one_response()
        server_certificate.add_get_server_certificate()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(server_certificate.resource)), 0)

    def test_create_server_certificate_wrong_chain(self):
        with open(ServerCertificateStubber.cert_file) as cert_file,\
                open(ServerCertificateStubber.key_file) as key_file,\
                open(ServerCertificateStubber.chain_file) as chain_file:

            with self.assertRaises(errors.Error) as cm:
                self.aws.add_server_certificate(
                    name='my-test-server-certificate',
                    certificate_body=chain_file.read(),  # to trigger error
                    private_key=key_file.read(),
                    certificate_chain=cert_file.read(),  # to trigger error
                )
            self.assertIn('Certificate does not match private_key', str(cm.exception))

    def test_create_server_certificate_bad_chain(self):
        with open(ServerCertificateStubber.cert_file) as cert_file,\
                open(ServerCertificateStubber.key_file) as key_file,\
                open(ServerCertificateStubber.bad_chain_file) as bad_chain_file:

            with self.assertRaises(errors.Error) as cm:
                self.aws.add_server_certificate(
                    name='my-test-server-certificate',
                    certificate_body=cert_file.read(),  # to trigger error
                    private_key=key_file.read(),
                    certificate_chain=bad_chain_file.read(),  # to trigger error
                )
            self.assertIn('Invalid chain for', str(cm.exception))


class TestDestroyServerCertificate(StubberTestCase):

    def test_destroy_server_certificate(self):
        goal = self.create_goal('destroy')

        server_certificate = self.fixtures.enter_context(ServerCertificateStubber(
            goal.get_service(
                self.aws.add_server_certificate(
                    name='my-test-server-certificate',
                ),
                'destroy',
            )
        ))
        server_certificate.add_list_server_certificate_one_response()
        server_certificate.add_get_server_certificate()
        server_certificate.add_list_server_certificate_one_response()
        server_certificate.add_get_server_certificate()
        server_certificate.add_delete_server_certificate()

        goal.execute()

    def test_destroy_server_certificate_idempotent(self):
        goal = self.create_goal('destroy')

        server_certificate = self.fixtures.enter_context(ServerCertificateStubber(
            goal.get_service(
                self.aws.add_server_certificate(
                    name='my-test-server-certificate',
                ),
                'destroy',
            )
        ))
        server_certificate.add_list_server_certificate_empty_response()
        server_certificate.add_list_server_certificate_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(server_certificate.resource)), 0)
