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

from . import aws


class TestHostedZone(aws.TestBasicUsage):

    def setUpResource(self):
        self.expected_resource_id = '/hostedzone/Z111111QQQQQQQ'
        self.resource = self.aws.add_hosted_zone(
            name='example.com',
        )

        self.responses.add_fixture(
            "GET",
            "https://route53.amazonaws.com/2013-04-01/hostedzone/Z111111QQQQQQQ/rrset",
            "aws_hosted_zone_rrset_0",
            expires=1,
        )

    # FIXME: Refactor tests so matching can be done in a generic way
    def test_no_change(self):
        self.responses.add_fixture("GET", "https://route53.amazonaws.com/2013-04-01/hostedzone", self.fixture_found, expires=1)
        self.assertRaises(errors.NothingChanged, self.runner.apply)
        self.assertEqual(self.target.resource_id, self.expected_resource_id)

    # FIXME: Refactor tests so matching can be done in a generic way
    def test_create(self):
        self.responses.add_fixture("GET", "https://route53.amazonaws.com/2013-04-01/hostedzone", self.fixture_404, expires=1)
        self.responses.add_fixture("POST", self.base_url, self.fixture_create, expires=1)
        self.responses.add_fixture("GET", "https://route53.amazonaws.com/2013-04-01/hostedzone", self.fixture_found)
        self.runner.apply()
        self.assertEqual(self.target.resource_id, self.expected_resource_id)
