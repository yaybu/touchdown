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

from __future__ import division

import logging
import time
import threading
from six.moves import queue

from . import errors


logger = logging.getLogger(__name__)


class SerialMap(object):

    def __init__(self, resources, callable, echo):
        self.resources = resources
        self.callable = callable
        self._echo = echo
        self.total = len(self.resources)
        self.current = 0

    def echo(self, text, **kwargs):
        self._echo("[{: >6.2%}] {}".format(
            self.current / self.total,
            text,
        ))

    def __iter__(self):
        plan = list(self.resources.all())
        for resource in plan:
            self.current += 1
            self.callable(self.echo, resource)
            yield self.current / self.total

    def __call__(self):
        list(iter(self))


class InteruptibleQueue(queue.Queue):

    def _init(self, maxsize):
        queue.Queue._init(self, maxsize)
        self.stopped = False

    def stop(self):
        self.stopped = True

    def __iter__(self):
        while not self.stopped:
            try:
                yield self.get(timeout=1)
                self.task_done()
            except queue.Empty:
                pass


class QueueOnce(InteruptibleQueue):

    def _init(self, maxsize):
        InteruptibleQueue._init(self, maxsize)
        self._items = set()

    def _put(self, item):
        if item not in self._items:
            InteruptibleQueue._put(self, item)
            self._items.add(item)


class ParallelMap(object):

    workers = 8
    ABORT = object()

    def __init__(self, resources, callable, echo):
        self.resources = resources
        self.callable = callable
        self._echo = echo

        self.ready = QueueOnce()
        self.done = InteruptibleQueue()
        self.active = set()

        self.total = len(self.resources)
        self.current = 0

    def echo(self, text, **kwargs):
        self._echo("[{: >6.2%}] [{}] {}".format(
            self.current / self.total,
            getattr(threading.current_thread(), "name", "leader"),
            text,
        ))

    def worker(self):
        for resource in self.ready:
            try:
                self.active.add(resource)
                try:
                    self.callable(self.echo, resource)
                finally:
                    self.active.remove(resource)
                self.done.put(resource)
            except errors.Error as e:
                self.echo("ERROR: {}. Stopping.".format(e))
                self.done.put(self.ABORT)
                self.ready.stop()
                continue
            except Exception:
                self.echo("ERROR: Unhandled error - stopping.")
                self.done.put(self.ABORT)
                self.ready.stop()
                raise

    def wait_for_remaining(self):
        # No more dependencies to process - we just need to wait for any
        # remaining tasks to complete
        remaining = None
        while len(self.active) > 0:
            if len(self.active) != remaining:
                remaining = len(self.active)
                self.current = self.total - remaining

                if remaining == 1:
                    self.echo("{} remaining".format(list(self.active)[0]))
                else:
                    self.echo("{} tasks remaining".format(remaining))
            time.sleep(1)
            yield self.current / self.total

    def __iter__(self):
        # Start up as many workers as requested.
        for i in range(self.workers):
            t = threading.Thread(target=self.worker, name="worker{}".format(i))
            t.start()

        # Seed the workers with the initial batch of work
        # These are all the tasks that have no dependencies
        for resource in self.resources.get_ready():
            self.ready.put(resource)

        # Now we block on the "done" queue. Resources put in the queue are
        # complete - so we can inform the dep solver and ask for any new work
        # that this might unblock.
        while not self.resources.empty():
            try:
                resource = self.done.get(timeout=1)
                if resource == self.ABORT:
                    break

                self.current += 1

                self.resources.complete(resource)
                for resource in self.resources.get_ready():
                    self.ready.put(resource)
                self.done.task_done()
            except queue.Empty:
                pass

            yield self.current / self.total

        for progress in self.wait_for_remaining():
            yield progress

        self.ready.stop()

    def __call__(self):
        list(iter(self))
