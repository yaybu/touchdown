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

from .errors import CycleError


class Runner(object):

    def __init__(self, node, ui):
        self.node = node
        self.ui = ui

    def _resolve(self, node, resolved, unresolved):
        unresolved.append(node)
        for dep in node.dependencies:
            if dep not in resolved:
                if dep in unresolved:
                    raise CycleError(
                        'Circular reference between %s and %s' % (node, dep)
                    )
                self._resolve(dep, resolved, unresolved)
        resolved.append(node)
        unresolved.remove(node)

    def _plan(self):
        resolved = []
        self._resolve(self.node, resolved, [])

        plan = []
        for resource in resolved:
            plan.append((resource, tuple(resource.policy.get_actions(self))))

        return plan

    def apply(self):
        plan = self._plan()

        if not self.ui.confirm_plan(plan):
            return

        for resource, actions in plan:
            for action in actions:
                # if not ui.confirm_action(action):
                #     continue
                action.run()
