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

import datetime
import time

from touchdown.aws import common
from touchdown.aws.logs import LogGroup
from touchdown.core import plan
from touchdown.core.datetime import as_seconds
from touchdown.core.utils import force_str


class Plan(common.SimplePlan, plan.Plan):

    name = 'tail'
    resource = LogGroup
    service_name = 'logs'

    def get_log_group_name(self):
        return self.resource.name

    def tail(self, start, end, follow):
        kwargs = {
            'logGroupName': self.get_log_group_name(),
        }
        if start:
            kwargs['startTime'] = as_seconds(start) * 1000
        if end:
            kwargs['endTime'] = as_seconds(end) * 1000

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
                    self.runner.ui.echo('[{timestamp}] [{logStreamName}] {message}'.format(**{
                        'logStreamName': event.get('logStreamName', ''),
                        'message': force_str(event['message'].encode('utf-8', 'ignore')),
                        'timestamp': datetime.datetime.utcfromtimestamp(int(event['timestamp']) / 1000.0),
                    }))
                    kwargs['startTime'] = event['timestamp']
                if 'nextToken' not in results:
                    break
                filters['nextToken'] = results['nextToken']
                results = self.client.filter_log_events(**filters)
            return seen

        try:
            seen = pull(kwargs, set())
            while follow:
                seen = pull(kwargs, seen)
                time.sleep(2)
        except KeyboardInterrupt:
            pass
