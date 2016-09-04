# Copyright 2016 Isotoma Limited
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

# This code is not currently exposed publically. It is an example of how to
# stream from a aws log using the FilterLogEvents API.

import gzip

import six

from touchdown.aws import common
from touchdown.aws.cloudfront import Distribution
from touchdown.core import plan


class Plan(common.SimplePlan, plan.Plan):

    name = 'tail'
    resource = Distribution
    service_name = 's3'

    fields = [
        'date',
        'time',
        'x-edge-location',
        'sc-bytes',
        'c-ip',
        'cs-method',
        'cs(Host)',
        'cs-uri-stem',
        'sc-status',
        'cs(Referer)',
        'cs(User-Agent)',
        'cs-uri-query',
        'cs(Cookie)',
        'x-edge-result-type',
        'x-edge-request-id',
        'x-host-header',
        'cs-protocol',
        'cs-bytes',
        'time-taken',
        'x-forwarded-for',
        'ssl-protocol',
        'ssl-cipher',
        'x-edge-response-result-type',
    ]

    def tail(self, start, end, follow):
        if follow:
            print('Following is not supported for this stream')
            return

        if not self.resource.logging.enabled:
            print('Logging is not enabled for this CloudFront distribution')
            return

        pages = self.client.get_paginator('list_objects').paginate(
            Bucket=self.resource.logging.bucket.name,
            Prefix=self.resource.logging.prefix,
        )

        contents = []
        [contents.extend(p.get('Contents', [])) for p in pages]
        contents.sort(key=lambda c: c['LastModified'])

        if start:
            contents = filter(lambda c: c['LastModified'] >= start, contents)

        if end:
            contents = filter(lambda c: c['LastModified'] <= end, contents)

        print('#Version: 1.0')
        print('#Fields: {}'.format(' '.join(self.fields)))

        for log in contents:
            response = self.client.get_object(
                Bucket=self.resource.logging.bucket.name,
                Key=log['Key'],
            )

            with gzip.GzipFile(fileobj=six.BytesIO(response['Body'].read())) as f:
                blob = f.read()

            lines = blob.split(b'\n')
            for line in lines[2:]:
                print(line)
