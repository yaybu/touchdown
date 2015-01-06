import unittest
import mock
import textwrap

from touchdown.core import errors
from touchdown.core import workspace
from touchdown.core.runner import Runner
from touchdown.core.main import ConsoleInterface

from six import StringIO as BufferIO

from botocore.vendored.requests.exceptions import ConnectionError
from botocore.vendored.requests.adapters import HTTPAdapter
try:
    from botocore.vendored.requests.packages.urllib3.response import HTTPResponse
except ImportError:
    from urllib3.response import HTTPResponse
from botocore.endpoint import Endpoint as OldEndpoint


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

    def matches(self, request, mock):
        if callable(mock['match']):
            return mock['match'](request, mock)
        if request.url == mock['match']:
            return True

    def render(self, request, mock):
        if callable(mock['body']):
            mock = mock['body'](request, mock)

        body = BufferIO(mock['body'])

        headers = {
            "Content-Type": mock['content_type'],
        }
        headers.update(mock.get('headers', {}))

        response = self.build_response(request, HTTPResponse(
            status=mock['status'],
            body=body,
            headers=headers,
            preload_content=False,
        ))

        if not mock.get('stream'):
            response.content  # noqa

        if mock['expires']:
            mock['expires'] = mock['expires'] - 1
            if not mock['expires']:
                self.mocks.remove(mock)

        return response

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        for mock in self.mocks:
            if self.matches(request, mock):
                response = self.render(request, mock)
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
        self.aws = self.workspace.add_aws(access_key_id='dummy', region='eu-west-1')
        self.runner = Runner(self.workspace, ConsoleInterface(interactive=False))

    def tearDown(self):
        self._patcher.stop()
