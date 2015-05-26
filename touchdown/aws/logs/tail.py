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

# This code is not currently exposed publically. It is an example of how to
# stream from a aws log using the FilterLogEvents API.

import time

from touchdown.core import plan
from touchdown.core.datetime import as_seconds
from touchdown.aws import common
from touchdown.aws.logs import LogGroup


class Plan(common.SimplePlan, plan.Plan):

    name = "tail"
    resource = LogGroup
    service_name = "logs"

    def tail(self, start, end, follow):
        kwargs = {
            'logGroupName': self.resource.name,
        }
        if start:
            kwargs['startTime'] = as_seconds(start)
        if end:
            kwargs['endTime'] = as_seconds(end)

        def pull(kwargs, previous_events):
            seen = set()
            filters = {}
            filters.update(kwargs)
            results = self.client.filter_log_events(**filters)
            while True:
                for event in results.get('events', []):
                    seen.add(event['eventId'])
                    if event['eventId'] in previous_events:
                        continue
                    print(u"[{logStreamName}] {message}".format(**event))
                    kwargs['startTime'] = event['timestamp']
                if 'nextToken' not in results:
                    break
                filters['nextToken'] = results['nextToken']
                results = self.client.filter_log_events(**filters)
            return seen

        seen = pull(kwargs, set())
        while follow:
            seen = pull(kwargs, seen)
            time.sleep(2)
