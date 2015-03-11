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
from threading import Thread
from six.moves import queue

from . import errors, goals


logger = logging.getLogger(__name__)


class Runner(object):

    def __init__(self, goal, workspace, ui):
        try:
            self.goal = goals.Goal.goals[goal](workspace, ui)
        except KeyError:
            raise errors.Error("No such goal '{}'".format(goal))

        self.workspace = workspace
        self.ui = ui
        self.resources = {}

    def dot(self):
        graph = ["digraph ast {"]

        for node, deps in self.goal.get_plan_order().items():
            if not node.dot_ignore:
                graph.append('{} [label="{}"];'.format(id(node), node))
                for dep in deps:
                    if not dep.dot_ignore:
                        graph.append("{} -> {};".format(id(node), id(dep)))

        graph.append("}")
        return "\n".join(graph)

    def plan(self):
        self.goal.plan(self.ui)

        for resource in self.goal.get_execution_order().all():
            changes = self.goal.get_changes(resource)
            if changes:
                yield resource, changes

    def apply_resource(self, progress, resource):
        for change in self.goal.get_changes(resource):
            description = list(change.description)
            self.ui.echo("[{: >6.2%}] [{}] {}".format(progress, resource, description[0]))
            for line in description[1:]:
                self.ui.echo("[{: >6.2%}] [{}]     {}".format(progress, resource, line))
            change.run()

    def apply_resources(self):
        plan = list(self.goal.get_execution_order().all())
        for i, resource in enumerate(plan):
            progress = i / len(plan)
            self.apply_resource(progress, resource)

    def apply(self):
        plan = list(self.plan())

        if not len(plan):
            raise errors.NothingChanged()

        if not self.ui.confirm_plan(plan):
            return

        self.apply_resources()


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


class ThreadedRunner(Runner):

    workers = 8

    def apply_resources(self):
        ready = QueueOnce()
        done = InteruptibleQueue()
        active = set()
        ABORT = object()

        map = self.goal.get_execution_order()
        total = len(map)
        current = 0

        # A worker thread just pops stuff off the queue and passes it
        # to self.apply_resource()
        def worker():
            for resource in ready:
                try:
                    active.add(resource)
                    try:
                        self.apply_resource(current / total, resource)
                    finally:
                        active.remove(resource)
                    done.put(resource)
                except errors.Error as e:
                    self.ui.echo("[{: >6.2%}] [{}] ERROR: {}. Stopping.".format(current / total, resource, e))
                    done.put(ABORT)
                    ready.stop()
                    continue
                except Exception:
                    self.ui.echo("ERROR: Unhandled error - stopping.")
                    done.put(ABORT)
                    ready.stop()
                    raise

        # Start up as many workers as requested.
        for i in range(self.workers):
            t = Thread(target=worker, name="worker{}".format(i))
            t.daemon = True
            t.start()

        # Seed the workers with the initial batch of work
        # These are all the tasks that have no dependencies
        for resource in map.get_ready():
            ready.put(resource)

        # Now we block on the "done" queue. Resources put in the queue are
        # complete - so we can inform the dep solver and ask for any new work
        # that this might unblock.
        while not map.empty():
            try:
                resource = done.get(timeout=1)
                if resource == ABORT:
                    break

                current += 1

                map.complete(resource)
                for resource in map.get_ready():
                    ready.put(resource)
                done.task_done()
            except queue.Empty:
                pass

        # No more dependencies to process - we just need to wait for any
        # remaining tasks to complete
        remaining = None
        while len(active) > 0:
            if len(active) != remaining:
                remaining = len(active)
                if remaining == 1:
                    self.ui.echo("{} remaining".format(list(active)[0]))
                else:
                    self.ui.echo("{} tasks remaining".format(remaining))
            time.sleep(1)
