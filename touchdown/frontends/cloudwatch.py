# Copyright 2014 Isotoma Limited
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

from .noninteractive import NonInteractiveFrontend


def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx+n, l)]


class CloudWatchFrontend(NonInteractiveFrontend):

    def __init__(self, group, stream, batch_size=10000, wait=30):
        self.group = group
        self.stream = stream
        self.batch_size = min(batch_size, 10000)
        self.wait = wait
        self.events = []
        self.last_echo = self.last_send = datetime.datetime.now()

    def _echo(self, text, nl=True, **kwargs):
        self.events.append({
            "Message": text,
            "Timestamp": datetime.datetime.now(),
        })
        if self._should_send():
            self._send()

    def finish(self):
        if self.events:
            self._send()

    def _should_send(self):
        if len(self.events) > self.batch_size:
            return True
        if (self.last_echo - self.last_send).total_seconds() > self.wait:
            return True
        return False

    def _send(self):
        events, self.events = self.events, []
        for events_batch in batch(events, self.batch_size):
            self.client.put_log_events(
                events=events_batch,
                logGroupName=self.group,
                logStreamName=self.stream,
            )
