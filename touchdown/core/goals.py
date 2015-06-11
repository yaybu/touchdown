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
import os

from . import dependencies, plan, map, errors
from .cache import JSONFileCache


class GoalFactory(object):

    def __init__(self):
        self.goals = {}

    def register(self, cls):
        self.goals[cls.name] = cls

    def registered(self):
        return self.goals.items()

    def create(self, name, workspace, ui, map=map.ParallelMap):
        try:
            goal_class = self.goals[name]
        except KeyError:
            raise errors.Error("No such goal '{}'".format(name))
        return goal_class(workspace, ui, map=map)


class Goal(object):

    execute_in_reverse = False

    def __init__(self, workspace, ui, map=map.ParallelMap, cache=None):
        self.ui = ui
        self.cache = cache
        if not self.cache:
            self.cache = JSONFileCache(os.path.expanduser('~/.touchdown'))
        self.workspace = workspace
        self.resources = {}
        self.Map = map

    @classmethod
    def setup_argparse(cls, parser):
        pass

    def get_plan_order(self):
        return dependencies.DependencyMap(self.workspace, tips_first=False)

    def get_plan_class(self, resource):
        raise NotImplementedError(self.get_plan_class)

    def get_plan(self, resource):
        if resource not in self.resources:
            klass = self.get_plan_class(resource)
            plan = klass(self, resource)
            plan.validate()
            self.resources[resource] = plan
        return self.resources[resource]

    def get_execution_order(self):
        return dependencies.DependencyMap(self.workspace, tips_first=self.execute_in_reverse)

    def collect_as_iterable(self, plan_name):
        collected = []

        def _(echo, resource):
            plan = self.get_plan(resource)
            if plan.name == plan_name:
                collected.append(plan)
        for progress in self.Map(self.get_plan_order(), _, self.ui.echo):
            self.ui.echo("\r[{: >6.2%}] Building plan...".format(progress), nl=False)
        self.ui.echo("")
        return collected

    def collect_as_dict(self, plan_name):
        collected = {}

        def _(echo, resource):
            plan = self.get_plan(resource)
            if plan.name == plan_name:
                collected[plan.resource.name] = plan
        for progress in self.Map(self.get_plan_order(), _, self.ui.echo):
            self.ui.echo("\r[{: >6.2%}] Building plan...".format(progress), nl=False)
        self.ui.echo("")
        return collected


class Describe(Goal):

    name = "describe"

    def get_plan_class(self, resource):
        return resource.meta.plans.get("describe", plan.NullPlan)


goals = GoalFactory()
register = goals.register
registered = goals.registered
create = goals.create

register(Describe)
