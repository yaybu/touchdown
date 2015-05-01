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

from . import dependencies, plan


class GoalFactory(object):

    def __init__(self):
        self.goals = {}

    def register(self, cls):
        self.goals[cls.name] = cls

    def create(self, name, workspace, ui):
        return self.goals[name](workspace, ui)


class Goal(object):

    execute_in_reverse = False

    def __init__(self, workspace, ui):
        self.ui = ui
        self.workspace = workspace
        self.resources = {}
        self.reset_changes()

    def reset_changes(self):
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
        if resource not in self.changes:
            self.changes[resource] = list(self.get_plan(resource).get_actions())
        return self.changes[resource]

    def is_stale(self):
        return len(self.changes) != 0

    def get_execution_order(self):
        return dependencies.DependencyMap(self.workspace, tips_first=self.execute_in_reverse)


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
        if "never-destroy" not in resource.policies:
            return resource.meta.plans.get("destroy", resource.meta.plans.get("describe", plan.NullPlan))
        return resource.meta.plans.get("describe", plan.NullPlan)


goals = GoalFactory()
goals.register(Describe)
goals.register(Apply)
goals.register(Destroy)
