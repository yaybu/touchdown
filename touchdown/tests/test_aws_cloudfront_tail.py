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

import gzip

import six
from botocore.response import StreamingBody

from touchdown.core.datetime import now
from touchdown.tests.aws import StubberTestCase
from touchdown.tests.stubs.aws import DistributionStubber


class TestDistributionTail(StubberTestCase):

    def test_tail_no_follow(self):
        goal = self.create_goal('tail')

        self.fixtures.enter_context(DistributionStubber(
            goal.get_service(
                self.aws.get_distribution(
                    name='www.example.com',
                ),
                'tail',
            )
        ))

        goal.execute('www.example.com', None, None, True)

    def test_tail_no_logging(self):
        goal = self.create_goal('tail')

        self.fixtures.enter_context(DistributionStubber(
            goal.get_service(
                self.aws.get_distribution(
                    name='www.example.com',
                ),
                'tail',
            )
        ))

        goal.execute('www.example.com', None, None, False)

    def test_tail(self):
        goal = self.create_goal('tail')

        bucket = self.aws.get_bucket(name='my-log-bucket')

        distribution = self.fixtures.enter_context(DistributionStubber(
            goal.get_service(
                self.aws.get_distribution(
                    name='www.example.com',
                    logging={
                        'enabled': True,
                        'bucket': bucket,
                        'prefix': '/my/prefix',
                    },
                ),
                'tail',
            )
        ))

        distribution.add_response(
            'list_objects',
            service_response={
                'Contents': [{
                    'Key': 'log-chunk-1.gz',
                    'LastModified': now(),
                }]
            },
            expected_params={
                'Bucket': 'my-log-bucket',
                'Prefix': '/my/prefix',
            }
        )

        buf = six.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode='wb') as f:
            f.write(b'line1\nline2\nline3\n')
        log_chunk = buf.getvalue()

        distribution.add_response(
            'get_object',
            service_response={
                'Body': StreamingBody(
                    six.BytesIO(log_chunk),
                    len(log_chunk),
                ),
            },
            expected_params={
                'Bucket': 'my-log-bucket',
                'Key': 'log-chunk-1.gz',
            }
        )

        goal.execute('www.example.com', None, None, False)
