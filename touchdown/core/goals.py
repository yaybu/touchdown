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

from . import dependencies, plan, map, errors


class GoalFactory(object):

    def __init__(self):
        self.goals = {}

    def register(self, cls):
        self.goals[cls.name] = cls

    def create(self, name, workspace, ui, map=map.ParallelMap):
        try:
            goal_class = self.goals[name]
        except KeyError:
            raise errors.Error("No such goal '{}'".format(name))
        return goal_class(workspace, ui, map=map)


class Goal(object):

    execute_in_reverse = False

    def __init__(self, workspace, ui, map=map.ParallelMap):
        self.ui = ui
        self.workspace = workspace
        self.resources = {}
        self.Map = map

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

    def get_execution_order(self):
        return dependencies.DependencyMap(self.workspace, tips_first=self.execute_in_reverse)


class Describe(Goal):

    name = "describe"

    def get_plan_class(self, resource):
        return resource.meta.plans.get("describe", plan.NullPlan)


goals = GoalFactory()
register = goals.register
create = goals.create
register(Describe)
