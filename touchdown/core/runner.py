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

    def __init__(self, goal, node, ui):
        try:
            self.goal = goals.Goal.goals[goal]()
        except KeyError:
            raise errors.Error("No such goal '{}'".format(goal))

        self.node = node
        self.ui = ui
        self.resources = {}

    def get_plan(self, resource):
        if resource not in self.resources:
            klass = self.goal.get_planner(resource)
            self.resources[resource] = klass(self, resource)
        return self.resources[resource]

    def dot(self):
        graph = ["digraph ast {"]

        for node, deps in self.goal.get_dependency_map(self.node).items():
            if not node.dot_ignore:
                graph.append('{} [label="{}"];'.format(id(node), node))
                for dep in deps:
                    if not dep.dot_ignore:
                        graph.append("{} -> {};".format(id(node), id(dep)))

        graph.append("}")
        return "\n".join(graph)

    def plan(self):
        resolved = list(self.goal.get_dependency_map(self.node).all())
        plan = []
        with self.ui.progress(resolved, label="Creating change plan") as resolved:
            for resource in resolved:
                actions = tuple(self.get_plan(resource).get_actions())
                if not actions:
                    logger.debug("No actions for {} - skipping".format(resource))
                    continue
                plan.append((resource, actions))

        return plan

    def apply(self):
        plan = self.plan()

        if not plan:
            raise errors.NothingChanged()

        if not self.ui.confirm_plan(plan):
            return

        with self.ui.progress(plan, label="Apply changes") as plan:
            for resource, actions in plan:
                for action in actions:
                    # if not ui.confirm_action(action):
                    #     continue
                    action.run()
