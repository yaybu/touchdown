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
import threading
import time

from six.moves import queue

from . import errors

logger = logging.getLogger(__name__)


class SerialMap(object):

    def __init__(self, ui, resources, callable):
        self.ui = ui
        self.resources = resources
        self.callable = callable
        self.total = len(self.resources)

    def __iter__(self):
        plan = list(self.resources.all())
        for current, resource in enumerate(plan):
            self.callable(resource)
            yield current


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

    def __init__(self, ui, resources, callable):
        self.ui = ui
        self.resources = resources
        self.callable = callable

        self.ready = QueueOnce()
        self.done = InteruptibleQueue()
        self.active = set()

        self.total = len(self.resources)
        self.current = 0

    def worker(self):
        for resource in self.ready:
            try:
                self.active.add(resource)
                try:
                    self.callable(resource)
                finally:
                    self.active.remove(resource)
                self.done.put(resource)
            except BaseException as e:
                self.done.put(e)
                continue

    def pump_once(self):
        try:
            resource = self.done.get(timeout=1)
        except queue.Empty:
            return

        if isinstance(resource, BaseException):
            raise resource

        self.current += 1

        self.resources.complete(resource)
        for resource in self.resources.get_ready():
            self.ready.put(resource)
        self.done.task_done()

    def pump(self):
        # Now we block on the 'done' queue. Resources put in the queue are
        # complete - so we can inform the dep solver and ask for any new work
        # that this might unblock.
        while not self.resources.empty():
            self.pump_once()
            yield self.current

    def wait_for_remaining(self):
        # No more dependencies to process - we just need to wait for any
        # remaining tasks to complete
        remaining = None
        while len(self.active) > 0:
            if len(self.active) != remaining:
                remaining = len(self.active)
                self.current = self.total - remaining
            time.sleep(1)
            yield self.current

    def __iter__(self):
        caught_error = None
        try:
            # Start up as many workers as requested.
            for i in range(self.workers):
                t = threading.Thread(target=self.worker, name='worker{}'.format(i))
                t.start()

            # Seed the workers with the initial batch of work
            # These are all the tasks that have no dependencies
            for resource in self.resources.get_ready():
                self.ready.put(resource)

            for current in self.pump():
                yield current

        except errors.Error as e:
            caught_error = e
            self.ui.failure(str(e))
            self.ui.echo('Exiting...')

        except KeyboardInterrupt:
            self.ui.echo('Interrupted. Pending tasks cancelled.')

        except Exception as e:
            caught_error = e
            self.ui.echo('Unhandled error. Cleaning up.')

        finally:
            for current in self.wait_for_remaining():
                yield current
            self.ready.stop()

            if caught_error:
                raise caught_error

    def __call__(self):
        list(iter(self))
