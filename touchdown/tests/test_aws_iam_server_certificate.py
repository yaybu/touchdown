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
from touchdown.tests.stubs.aws import ServerCertificateStubber

from .fixtures.aws import RoleFixture


class TestCreateServerCertificate(StubberTestCase):

    def test_create_server_certificate(self):
        goal = self.create_goal('apply')

        role = self.fixtures.enter_context(RoleFixture(goal, self.aws))

        server_certificate = self.fixtures.enter_context(ServerCertificateStubber(
            goal.get_service(
                self.aws.add_server_certificate(
                    name='my-test-server-certificate',
                    certificate_body=open('host_omega.crt').read(),
                    private_key=open('host_omega.key').read(),
                ),
                'apply',
            )
        ))
        server_certificate.add_list_server_certificate_empty_response()
        server_certificate.add_list_server_certificate_empty_response()
        server_certificate.add_upload_server_certificate()
        server_certificate.add_list_server_certificate_empty_response()
        server_certificate.add_list_server_certificate_empty_response()
        server_certificate.add_list_server_certificate_empty_response()

        goal.execute()

    def test_create_server_certificate_idempotent(self):
        goal = self.create_goal('apply')

        role = self.fixtures.enter_context(RoleFixture(goal, self.aws))

        server_certificate = self.fixtures.enter_context(ServerCertificateStubber(
            goal.get_service(
                self.aws.add_server_certificate(
                    name='my-test-profile',
                    roles=[role],
                ),
                'apply',
            )
        ))
        server_certificate.add_list_instance_profile_one_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(server_certificate.resource)), 0)


class TestDestroyServerCertificate(StubberTestCase):

    def test_destroy_server_certificate(self):
        goal = self.create_goal('destroy')

        role = self.fixtures.enter_context(RoleFixture(goal, self.aws))

        server_certificate = self.fixtures.enter_context(ServerCertificateStubber(
            goal.get_service(
                self.aws.add_server_certificate(
                    name='my-test-profile',
                    roles=[role],
                ),
                'destroy',
            )
        ))
        server_certificate.add_list_instance_profile_one_response()
        server_certificate.add_remove_role_from_instance_profile()
        server_certificate.add_delete_instance_profile()

        goal.execute()

    def test_destroy_role_idempotent(self):
        goal = self.create_goal('destroy')

        server_certificate = self.fixtures.enter_context(ServerCertificateStubber(
            goal.get_service(
                self.aws.add_server_certificate(
                    name='my-test-profile',
                ),
                'destroy',
            )
        ))
        server_certificate.add_list_instance_profile_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(server_certificate.resource)), 0)
