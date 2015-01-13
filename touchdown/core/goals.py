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

from . import dependencies, errors, plan


class GoalType(type):

    def __new__(meta, class_name, bases, new_attrs):
        cls = type.__new__(meta, class_name, bases, new_attrs)
        if hasattr(cls, "name"):
            cls.goals[cls.name] = cls
        return cls


class Goal(six.with_metaclass(GoalType)):

    goals = {}
    tips_first = False

    def get_dependency_map(self, resource):
        return dependencies.DependencyMap(resource, tips_first=self.tips_first)

    def get_planner(self, resource):
        raise NotImplementedError(self.get_planner)


class Describe(Goal):

    name = "describe"

    def get_planner(self, resource):
        return resource.plans["describe"]


class Apply(Goal):

    name = "apply"

    def get_planner(self, resource):
        if "destroy" in resource.policies:
            if not "destroy" in resource.planners:
                raise errors.Error("Requested that {} should be destroyed, but this change is not supported".format(resource))
            return resource.plans["destroy"]

        if "never-create" in resource.policies:
            return resource.plans["describe"]

        return resource.plans.get("apply", resource.plans.get("describe", plan.NullPlan))


class Destroy(Goal):

    name = "destroy"
    tips_first = True

    def get_planner(self, resource):
        if not "never-destroy" in resource.policies:
            return resource.plans.get("destroy", plan.NullPlan)
        return plan.NullPlan
