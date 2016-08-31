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

from touchdown.core import errors


class ActionGoalMixin(object):

    mutator = True

    def __init__(self, *args, **kwargs):
        super(ActionGoalMixin, self).__init__(*args, **kwargs)
        self.reset_changes()

    def reset_changes(self):
        self.changes = {}

    def get_changes(self, resource):
        if resource not in self.changes:
            self.changes[resource] = list(self.get_plan(resource).get_actions())
        return self.changes[resource]

    def plan(self):
        self.reset_changes()
        self.visit(
            'Building plan...',
            self.get_plan_order(),
            self.get_changes,
        )
        for resource in self.get_execution_order().all():
            changes = self.get_changes(resource)
            if changes:
                yield resource, changes

    def apply_resource(self, resource):
        for change in self.get_changes(resource):
            description = list(change.description)
            self.ui.echo('[{}] {}'.format(resource, description[0]))
            for line in description[1:]:
                self.ui.echo('[{}]     {}'.format(resource, line))
            change.run()

    def apply_resources(self):
        dep_map = self.get_execution_order()
        with self.ui.progressbar(max_value=len(dep_map)) as pb:
            for status in self.Map(self.ui, dep_map, self.apply_resource):
                pb.update(status)

    def is_stale(self):
        return len(self.changes) != 0

    def execute(self):
        plan = list(self.plan())

        if not len(plan):
            raise errors.NothingChanged('Planning stage found no changes were required.')

        if not self.ui.confirm_plan(plan):
            return

        self.apply_resources()
