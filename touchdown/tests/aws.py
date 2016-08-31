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

import mock
from botocore.stub import Stubber as BaseStubber

from touchdown.tests.testcases import WorkspaceTestCase


class StubberTestCase(WorkspaceTestCase):

    def setUp(self):
        super(StubberTestCase, self).setUp()
        self.aws = self.workspace.add_aws(
            access_key_id='dummy',
            secret_access_key='dummy',
            region='eu-west-1',
        )
        self.fixtures.enter_context(mock.patch('time.sleep'))


class Stubber(BaseStubber):
    '''Extends the stubber from botocore so that it always asserts that
    there are no leftover responses.

    So, for eg:

    stub = Stubber(client)
    stub.add_response('get_abc', service_response={'a': 'b'})
    with stub:
        pass

    By using this stubber, the above will fail because there is a
    pending resquest. The botocore's stubber doesn't - you have to
    remember to call `stub.assert_no_pending_responses()`.

    '''

    def __exit__(self, exc_type, exc_value, traceback):
        super(Stubber, self).__exit__(exc_type, exc_value, traceback)
        # Only do this check if we are exiting cleanly, otherwise we
        # mask the actual exception.
        if exc_type is None:
            self.assert_no_pending_responses()
