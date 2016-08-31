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

from . import dependencies, errors, map
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
            raise errors.Error('No such goal "{}"'.format(name))
        return goal_class(workspace, ui, map=map)


class Goal(object):

    execute_in_reverse = False
    mutator = False

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
        # FIXME: Deprecated
        klass = self.get_plan_class(resource)
        return self.get_service(resource, klass.name)

    def get_service(self, resource, service):
        service_key = (resource, service)
        if service_key not in self.resources:
            klass = resource.meta.get_plan(service)
            service = klass(self, resource)
            service.validate()
            self.resources[service_key] = service
        return self.resources[service_key]

    def get_execution_order(self):
        return dependencies.DependencyMap(self.workspace, tips_first=self.execute_in_reverse)

    def visit(self, message, dep_map, callable):
        with self.ui.progressbar(max_value=len(dep_map)) as pb:
            for status in self.Map(self.ui, dep_map, callable):
                pb.update(status)

    def collect_as_iterable(self, plan_name):
        collected = []

        def _(resource):
            plan = self.get_plan(resource)
            if plan.name == plan_name:
                collected.append(plan)
        self.visit('Building plan...', self.get_plan_order(), _)
        return collected

    def collect_as_dict(self, plan_name):
        collected = {}

        def _(resource):
            plan = self.get_plan(resource)
            if plan.name == plan_name:
                collected[plan.resource.name] = plan
        self.visit('Building plan...', self.get_plan_order(), _)
        return collected


goals = GoalFactory()
register = goals.register
registered = goals.registered
create = goals.create
