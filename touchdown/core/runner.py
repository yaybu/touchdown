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

import logging

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

    def apply(self):
        plan = list(self.plan())

        if not len(plan):
            raise errors.NothingChanged()

        if not self.ui.confirm_plan(plan):
            return

        self.goal.apply(self.ui)
