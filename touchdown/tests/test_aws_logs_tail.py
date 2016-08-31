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

import datetime
import mock

from botocore.stub import ANY

from touchdown.core.datetime import now
from touchdown.tests.aws import StubberTestCase
from touchdown.tests.stubs.aws import LogGroupStubber


class TestLogGroupTailing(StubberTestCase):

    def test_tail_once(self):
        goal = self.create_goal('tail')

        log_group = self.fixtures.enter_context(LogGroupStubber(
            goal.get_service(
                self.aws.add_log_group(
                    name='test-log_group',
                ),
                'tail',
            )
        ))

        log_group.add_response(
            'filter_log_events',
            service_response={
                'events': [{
                    'eventId': 'EV1',
                    'timestamp': 0,
                    'logStreamName': 'logstream1',
                    'message': 'this is my message',
                }],
                'nextToken': 'nextToken1',
            },
            expected_params={
                'logGroupName': log_group.resource.name,
                'startTime': ANY,
                'endTime': ANY,
            }
        )

        log_group.add_response(
            'filter_log_events',
            service_response={
                'events': [{
                    'eventId': 'EV1',
                    'timestamp': 0,
                    'logStreamName': 'logstream1',
                    'message': 'this is my message',
                }, {
                    'eventId': 'EV2',
                    'timestamp': 0,
                    'logStreamName': 'logstream1',
                    'message': 'this is another message',
                }],
            },
            expected_params={
                'logGroupName': log_group.resource.name,
                'nextToken': 'nextToken1',
                'startTime': ANY,
                'endTime': ANY,
            }
        )

        echo = self.fixtures.enter_context(mock.patch.object(goal.ui, 'echo'))

        # Call with both a naive and non-naive datetime
        # The value is ignored but will at least trigger the dt handling
        # codepaths
        goal.execute(
            'test-log_group',
            start=datetime.datetime.now(),
            end=now(),
        )

        # Assert that pagination works and that de-duplication works
        echo.assert_has_calls([
            mock.call('[1970-01-01 00:00:00] [logstream1] this is my message'),
            mock.call('[1970-01-01 00:00:00] [logstream1] this is another message'),
        ])
