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

import calendar
import datetime
import threading
import time

from botocore.exceptions import ClientError

from six.moves import queue

from .base import BaseFrontend
from .progress import ProgressBar


class CloudWatchFrontend(BaseFrontend):

    def __init__(self, group, stream):
        super(CloudWatchFrontend, self).__init__()
        self.group = group
        self.stream = stream
        self.finished = False
        self.queue = queue.Queue()

    def _echo(self, text, nl=True, **kwargs):
        text = text.rstrip('\r\n')
        if text:
            self.queue.put({
                'message': text,
                'timestamp': calendar.timegm(datetime.datetime.utcnow().timetuple()) * 1000,
            })

    def start(self, subcommand, goal):
        self.plan = goal.get_plan(self.group)
        self.client = self.plan.client

        try:
            self.client.create_log_group(
                logGroupName=self.group.name,
            )
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') != 'ResourceAlreadyExistsException':
                raise

        try:
            self.client.create_log_stream(
                logGroupName=self.group.name,
                logStreamName=self.stream,
            )
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') != 'ResourceAlreadyExistsException':
                raise

        self.thread = threading.Thread(target=self._sender)
        self.thread.start()

    def finish(self):
        self.finished = True

    def _get_batch(self):
        batch = []
        for i in range(10000):
            try:
                item = self.queue.get_nowait()
            except queue.Empty:
                break
            batch.append(item)
        return batch

    def _get_batches(self):
        while True:
            batch = self._get_batch()
            if not batch:
                return
            yield batch

    def _send(self):
        for batch in self._get_batches():
            kwargs = dict(
                logEvents=batch,
                logGroupName=self.group.name,
                logStreamName=self.stream,
            )
            if self.sequence_token:
                kwargs['sequenceToken'] = self.sequence_token
            response = self.client.put_log_events(**kwargs)
            self.sequence_token = response['nextSequenceToken']

    def _sender(self):
        self.sequence_token = None
        while not self.finished:
            self._send()
            time.sleep(1)
        self._send()

    def progressbar(self, **kwargs):
        return ProgressBar(self, **kwargs)

    def prompt(self, message, key=None, default=None):
        retval = super(CloudWatchFrontend, self).prompt(message, key, default)
        if retval:
            return retval
        return default

    def confirm(self, message):
        return True
