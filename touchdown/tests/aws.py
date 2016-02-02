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

import json
import os
import unittest

import mock
import six
import vcr
from botocore.endpoint import Endpoint as OldEndpoint
from botocore.vendored.requests.adapters import HTTPAdapter
from botocore.vendored.requests.exceptions import ConnectionError

from touchdown.core import errors, goals, workspace
from touchdown.core.map import SerialMap
from touchdown.core.utils import force_bytes
from touchdown.frontends import ConsoleFrontend

try:
    from contextlib import ExitStack
except ImportError:
    from contextlib2 import ExitStack


try:
    from botocore.vendored.requests.packages.urllib3.response import HTTPResponse
except ImportError:
    from urllib3.response import HTTPResponse


PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


class Buffer(object):

    def __init__(self, contents):
        self.contents = contents

    def makefile(self, *args, **kwargs):
        return six.BytesIO(force_bytes(self.contents))


class TestAdapter(HTTPAdapter):

    def __init__(self):
        super(TestAdapter, self).__init__()
        self.mocks = []
        self.calls = []

    def add(self, method, match, body, status=200, stream=False, content_type='text/plain', headers=None, expires=None):
        self.mocks.append(dict(
            method=method,
            match=match,
            body=body,
            status=status,
            stream=stream,
            content_type=content_type,
            headers=headers,
            expires=expires,
        ))

    def add_fixture(self, method, match, fixture, stream=False, expires=None):
        with open(os.path.join(os.path.dirname(__file__), "fixtures", fixture)) as fp:
            response = six.moves.http_client.HTTPResponse(Buffer(fp.read()))
            response.begin()

        headers = dict(response.getheaders())

        self.add(
            method,
            match,
            body=response.read(),
            status=response.status,
            stream=stream,
            content_type=response.getheader('Content-Type', 'text/plain'),
            headers=headers,
            expires=expires,
        )

    def matches(self, request, m):
        if callable(m['match']):
            return m['match'](request, m)
        if request.url == m['match']:
            return True

    def render(self, request, m):
        if callable(m['body']):
            m = m['body'](request, m)

        body = six.BytesIO(force_bytes(m['body']))

        headers = {
            "Content-Type": m['content_type'],
        }
        headers.update(m.get('headers', {}))

        response = self.build_response(request, HTTPResponse(
            status=m['status'],
            body=body,
            headers=headers,
            preload_content=False,
        ))

        if not m.get('stream'):
            response.content  # noqa

        if m['expires']:
            m['expires'] = m['expires'] - 1
            if not m['expires']:
                self.mocks.remove(m)

        return response

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        for m in self.mocks:
            if self.matches(request, m):
                response = self.render(request, m)
                self.calls.append((request, response))
                return response

        response = ConnectionError("Connection refused: {0}".format(request.url))
        self.calls.append((request, response))
        raise response


class TestCase(unittest.TestCase):

    def setUp(self):
        self.responses = TestAdapter()

        class TestEndpoint(OldEndpoint):

            responses = self.responses

            def __init__(self, *args, **kwargs):
                OldEndpoint.__init__(self, *args, **kwargs)
                self.http_session.mount('https://', self.responses)

        self._patcher = mock.patch('botocore.endpoint.Endpoint', TestEndpoint)
        self._patcher.start()

        self.workspace = workspace.Workspace()
        self.aws = self.workspace.add_aws(access_key_id='dummy', secret_access_key='dummy', region='eu-west-1')
        self.goal = goals.create(
            "apply",
            self.workspace,
            ConsoleFrontend(interactive=False),
            map=SerialMap
        )

    def tearDown(self):
        self._patcher.stop()


class TestBasicUsage(TestCase):

    def setUp(self):
        super(TestBasicUsage, self).setUp()

        self.setUpResource()

        self.fixture_found = "aws_{}_describe".format(self.resource.resource_name)
        self.fixture_404 = "aws_{}_describe_404".format(self.resource.resource_name)
        self.fixture_create = "aws_{}_create".format(self.resource.resource_name)

        self.plan = self.goal.get_plan(self.resource)
        self.base_url = 'https://{}.eu-west-1.amazonaws.com/'.format(self.plan.service_name)

    def setUpResource(self):
        raise NotImplementedError(self.setUpResource)

    def test_no_change(self):
        self.responses.add_fixture("POST", self.base_url, self.fixture_found, expires=1)
        self.assertRaises(errors.NothingChanged, self.goal.execute)
        self.assertEqual(self.plan.resource_id, self.expected_resource_id)

    def test_create(self):
        self.responses.add_fixture("POST", self.base_url, self.fixture_404, expires=1)
        self.responses.add_fixture("POST", self.base_url, self.fixture_create, expires=1)
        self.responses.add_fixture("POST", self.base_url, self.fixture_found)
        self.goal.execute()
        self.assertEqual(self.plan.resource_id, self.expected_resource_id)


class RecordedBotoCoreTest(unittest.TestCase):

    def patches(self):
        try:
            import botocore.vendored.requests.packages.urllib3.connectionpool as cpool
        except ImportError:  # pragma: no cover
            return ()
        from vcr.stubs.requests_stubs import VCRRequestsHTTPConnection, VCRRequestsHTTPSConnection

        return (
            (cpool, 'VerifiedHTTPSConnection', VCRRequestsHTTPSConnection),
            (cpool, 'VerifiedHTTPSConnection', VCRRequestsHTTPSConnection),
            (cpool, 'HTTPConnection', VCRRequestsHTTPConnection),
            (cpool, 'HTTPSConnection', VCRRequestsHTTPSConnection),
            (cpool.HTTPConnectionPool, 'ConnectionCls', VCRRequestsHTTPConnection),
            (cpool.HTTPSConnectionPool, 'ConnectionCls', VCRRequestsHTTPSConnection),
        )

    def _before_record_request(self, request):
        return request

    def _before_record_response(self, response):
        response['body']['string'] = response['body']['string'].replace(
            force_bytes(self.config["OWNER"]),
            b"x0x0x0x0x0x0",
        )
        return response

    def setUp(self):
        self.stack = ExitStack()

        self.config = {
            "OWNER": "x0x0x0x0x0x0",
            "ACCESS_KEY_ID": "AKIAI634JOB5PNTJNTZOOBA",
            "SECRET_ACCESS_KEY": "1234567890abcedfghijklmnopqrstuvwxyz!",
        }
        aws_json = os.path.join(PROJECT_ROOT, "aws.json")
        if os.path.exists(aws_json):
            with open(aws_json, "r") as fp:
                self.config.update(json.load(fp))

        self.vcr = vcr.VCR(
            before_record=self._before_record_request,
            before_record_response=self._before_record_response,
        )

        self.stack.enter_context(self.vcr.use_cassette(
            os.path.join(os.path.dirname(__file__), 'cassettes/{}.yml'.format(self.id())),
            # serializer='json',
            custom_patches=self.patches(),
            filter_headers=[
                'authorization',
                'date',
                "User-Agent",
                "X-Amz-Date",
            ],
        ))

        is_conn_dropped = self.stack.enter_context(mock.patch(
            'botocore.vendored.requests.packages.urllib3.connectionpool.is_connection_dropped',
        ))
        is_conn_dropped.return_value = True

        self.workspace = workspace.Workspace()
        self.aws = self.workspace.add_aws(
            region='eu-west-1',
            access_key_id=self.config['ACCESS_KEY_ID'],
            secret_access_key=self.config['SECRET_ACCESS_KEY'],
        )

    def tearDown(self):
        self.stack.close()

    def apply(self, assert_idempotent=True):
        self.apply_runner = goals.create("apply", self.workspace, ConsoleFrontend(interactive=False), map=SerialMap)
        self.apply_runner.execute()
        if assert_idempotent:
            self.assertRaises(errors.NothingChanged, self.apply_runner.execute)

    def destroy(self):
        self.destroy_runner = goals.create("destroy", self.workspace, ConsoleFrontend(interactive=False), map=SerialMap)
        self.destroy_runner.execute()
        self.assertRaises(errors.NothingChanged, self.destroy_runner.execute)
