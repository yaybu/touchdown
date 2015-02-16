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

import six

from . import dependencies, plan


class GoalType(type):

    def __new__(meta, class_name, bases, new_attrs):
        cls = type.__new__(meta, class_name, bases, new_attrs)
        if hasattr(cls, "name"):
            cls.goals[cls.name] = cls
        return cls


class Goal(six.with_metaclass(GoalType)):

    goals = {}
    execute_in_reverse = False

    def __init__(self, workspace, ui):
        self.ui = ui
        self.workspace = workspace
        self.resources = {}
        self.changes = {}

    def get_plan_order(self):
        return dependencies.DependencyMap(self.workspace, tips_first=False)

    def get_plan_class(self, resource):
        raise NotImplementedError(self.get_planner)

    def get_plan(self, resource):
        if resource not in self.resources:
            klass = self.get_plan_class(resource)
            plan = klass(self, resource)
            plan.validate()
            self.resources[resource] = plan
        return self.resources[resource]

    def get_changes(self, resource):
        if not resource in self.changes:
            self.changes[resource] = list(self.get_plan(resource).get_actions())
        return self.changes[resource]

    def plan(self, ui):
        self.changes = {}
        resolved = list(self.get_plan_order().all())
        with ui.progress(resolved, label="Creating change plan") as resolved:
            for resource in resolved:
                self.get_changes(resource)

    def is_stale(self):
        return len(self.changes) != 0

    def get_execution_order(self):
        return dependencies.DependencyMap(self.workspace, tips_first=self.execute_in_reverse)

    def apply(self, ui):
        plan = list(self.get_execution_order().all())
        with ui.progress(plan, label="Apply changes") as plan:
            for resource in plan:
                for change in self.get_changes(resource):
                    # if not ui.confirm_action(change):
                    #     continue
                    change.run()


class Describe(Goal):

    name = "describe"

    def get_plan_class(self, resource):
        return resource.meta.plans.get("describe", plan.NullPlan)


class Apply(Goal):

    name = "apply"

    def get_plan_class(self, resource):
        if "destroy" in resource.policies:
            return resource.meta.plans["destroy"]

        if "never-create" in resource.policies:
            return resource.meta.plans["describe"]

        return resource.meta.plans.get("apply", resource.meta.plans.get("describe", plan.NullPlan))


class Destroy(Goal):

    name = "destroy"
    execute_in_reverse = True

    def get_plan_class(self, resource):
        if not "never-destroy" in resource.policies:
            return resource.meta.plans.get("destroy", resource.meta.plans.get("describe", plan.NullPlan))
        return resource.meta.plans.get("describe", plan.NullPlan)
