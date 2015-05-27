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


class TestHostedZone(aws.TestCase):

    def setUp(self):
        super(TestHostedZone, self).setUp()

        self.fixture_found = "aws_hosted_zone_describe"
        self.fixture_404 = "aws_hosted_zone_describe_404"
        self.fixture_create = "aws_hosted_zone_create"
        self.base_url = 'https://route53.amazonaws.com/'

    def test_no_change(self):
        self.expected_resource_id = '/hostedzone/Z111111QQQQQQQ'
        self.resource = self.aws.add_hosted_zone(
            name='example.com',
        )
        self.plan = self.goal.get_plan(self.resource)

        self.responses.add_fixture(
            "GET",
            "https://route53.amazonaws.com/2013-04-01/hostedzone/Z111111QQQQQQQ/rrset",
            "aws_hosted_zone_rrset_0",
        )
        self.responses.add_fixture("GET", "https://route53.amazonaws.com/2013-04-01/hostedzone", self.fixture_found)
        self.assertRaises(errors.NothingChanged, self.goal.execute)
        self.assertEqual(self.plan.resource_id, self.expected_resource_id)

    def test_no_change_1(self):
        self.expected_resource_id = '/hostedzone/Z111111QQQQQQQ'
        self.resource = self.aws.add_hosted_zone(
            name='example.com',
            records=[{
                "name": "example.com.",
                "type": "A",
                "ttl": 900,
                "values": ['127.0.0.1'],
            }]
        )
        self.plan = self.goal.get_plan(self.resource)

        self.responses.add_fixture(
            "GET",
            "https://route53.amazonaws.com/2013-04-01/hostedzone/Z111111QQQQQQQ/rrset",
            "aws_hosted_zone_rrset_1",
        )
        self.responses.add_fixture(
            "GET",
            "https://route53.amazonaws.com/2013-04-01/hostedzone/Z111111QQQQQQQ/rrset/",
            "aws_hosted_zone_rrset_1",
        )
        self.responses.add_fixture("GET", "https://route53.amazonaws.com/2013-04-01/hostedzone", self.fixture_found)
        self.assertRaises(errors.NothingChanged, self.goal.execute)
        self.assertEqual(self.plan.resource_id, self.expected_resource_id)

    # FIXME: Refactor tests so matching can be done in a generic way
    def test_create(self):
        self.expected_resource_id = '/hostedzone/Z111111QQQQQQQ'
        self.resource = self.aws.add_hosted_zone(
            name='example.com',
        )
        self.plan = self.goal.get_plan(self.resource)

        self.responses.add_fixture(
            "GET",
            "https://route53.amazonaws.com/2013-04-01/hostedzone/Z111111QQQQQQQ/rrset",
            "aws_hosted_zone_rrset_0",
        )
        self.responses.add_fixture("GET", "https://route53.amazonaws.com/2013-04-01/hostedzone", self.fixture_404, expires=1)
        self.responses.add_fixture("POST", self.base_url, self.fixture_create, expires=1)
        self.responses.add_fixture("GET", "https://route53.amazonaws.com/2013-04-01/hostedzone", self.fixture_found)
        self.goal.execute()
        self.assertEqual(self.plan.resource_id, self.expected_resource_id)

    def test_add_rrset(self):
        self.expected_resource_id = '/hostedzone/Z111111QQQQQQQ'
        self.resource = self.aws.add_hosted_zone(
            name='example.com',
            records=[{
                "name": "example.com.",
                "type": "A",
                "ttl": 900,
                "values": ['127.0.0.1'],
            }]
        )
        self.plan = self.goal.get_plan(self.resource)

        self.responses.add_fixture(
            "GET",
            "https://route53.amazonaws.com/2013-04-01/hostedzone/Z111111QQQQQQQ/rrset",
            "aws_hosted_zone_rrset_0",
        )
        self.responses.add_fixture(
            "POST",
            "https://route53.amazonaws.com/2013-04-01/hostedzone/Z111111QQQQQQQ/rrset/",
            "aws_hosted_zone_rrset_change",
        )
        self.responses.add_fixture("GET", "https://route53.amazonaws.com/2013-04-01/hostedzone", self.fixture_found)
        self.goal.execute()
        self.assertEqual(self.plan.resource_id, self.expected_resource_id)

    def test_delete_rrset(self):
        self.expected_resource_id = '/hostedzone/Z111111QQQQQQQ'
        self.resource = self.aws.add_hosted_zone(
            name='example.com',
        )
        self.plan = self.goal.get_plan(self.resource)

        self.responses.add_fixture(
            "GET",
            "https://route53.amazonaws.com/2013-04-01/hostedzone/Z111111QQQQQQQ/rrset",
            "aws_hosted_zone_rrset_1",
        )
        self.responses.add_fixture(
            "POST",
            "https://route53.amazonaws.com/2013-04-01/hostedzone/Z111111QQQQQQQ/rrset/",
            "aws_hosted_zone_rrset_change",
        )
        self.responses.add_fixture("GET", "https://route53.amazonaws.com/2013-04-01/hostedzone", self.fixture_found)
        self.goal.execute()
        self.assertEqual(self.plan.resource_id, self.expected_resource_id)

    def test_update_rrset(self):
        self.expected_resource_id = '/hostedzone/Z111111QQQQQQQ'
        self.resource = self.aws.add_hosted_zone(
            name='example.com',
            records=[{
                "name": "example.com.",
                "type": "A",
                "ttl": 900,
                "values": ['192.168.0.1'],
            }]
        )
        self.plan = self.goal.get_plan(self.resource)

        self.responses.add_fixture(
            "GET",
            "https://route53.amazonaws.com/2013-04-01/hostedzone/Z111111QQQQQQQ/rrset",
            "aws_hosted_zone_rrset_1",
        )
        self.responses.add_fixture(
            "POST",
            "https://route53.amazonaws.com/2013-04-01/hostedzone/Z111111QQQQQQQ/rrset/",
            "aws_hosted_zone_rrset_change",
        )
        self.responses.add_fixture("GET", "https://route53.amazonaws.com/2013-04-01/hostedzone", self.fixture_found)
        self.goal.execute()
        self.assertEqual(self.plan.resource_id, self.expected_resource_id)
