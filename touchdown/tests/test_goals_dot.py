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

from touchdown.tests.testcases import WorkspaceTestCase


class TestDotGraphGeneration(WorkspaceTestCase):

    def test_generate_dot_graph(self):
        goal = self.create_goal('dot')

        aws = self.workspace.add_aws()
        vpc = aws.add_vpc(name='test-vpc')
        vpc.add_subnet(name='subnet-a')
        vpc.add_subnet(name='subnet-b')

        echo = self.fixtures.enter_context(mock.patch.object(goal.ui, 'echo'))
        goal.execute()

        # This should generate something like this:

        # digraph ast {
        #    4432359760 [label='vpc 'test-vpc''];
        #    4432359824 [label='subnet 'subnet-a''];
        #    4432359824 -> 4432359760;
        #    4432359888 [label='subnet 'subnet-b''];
        #    4432359888 -> 4432359760;
        # }

        # As id() output isn't stable between test runs we have to settle for:

        output = echo.call_args[0][0]
        assert output.startswith('digraph ast {')
        assert ' [label="vpc \'test-vpc\'"];' in output
        assert ' [label="subnet \'subnet-a\'"];' in output
        assert ' [label="subnet \'subnet-b\'"];' in output
        assert output.count(' -> ') == 2
        assert output.count(';') == 5
        assert output.endswith('}')
