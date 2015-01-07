import os
import unittest
import mock
import six

from touchdown.core import workspace
from touchdown.core.runner import Runner
from touchdown.core.main import ConsoleInterface
from touchdown.core.utils import force_bytes

from botocore.vendored.requests.exceptions import ConnectionError
from botocore.vendored.requests.adapters import HTTPAdapter
try:
    from botocore.vendored.requests.packages.urllib3.response import HTTPResponse
except ImportError:
    from urllib3.response import HTTPResponse
from botocore.endpoint import Endpoint as OldEndpoint


class Buffer(object):

    def __init__(self, contents):
        self.contents = contents

    def makefile(self, *args, **kwargs):
        return six.BytesIO(self.contents)


class TestAdapter(HTTPAdapter):

    def __init__(self):
        super(TestAdapter, self).__init__()
        self.mocks = []
        self.calls = []

    def add(self, method, match, body, status=200, stream=False, content_type='text/plain', expires=None):
        self.mocks.append(dict(
            method=method,
            match=match,
            body=body,
            status=status,
            stream=stream,
            content_type=content_type,
            expires=expires,
        ))

    def add_fixture(self, method, match, fixture, stream=False, expires=None):
        with open(os.path.join(os.path.dirname(__file__), "fixtures", fixture)) as fp:
            response = six.moves.http_client.HTTPResponse(Buffer(fp.read()))
            response.begin()

        self.add(
            method,
            match,
            body=response.read(),
            status=response.status,
            stream=stream,
            content_type=response.getheader('Content-Type', 'text/plain'),
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
        self.runner = Runner(self.workspace, ConsoleInterface(interactive=False))

    def tearDown(self):
        self._patcher.stop()
