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

from touchdown.core import plan
from touchdown.core.goals import Goal, register


class Tail(Goal):

    name = "tail"

    def get_plan_class(self, resource):
        return resource.meta.plans.get("tail", plan.NullPlan)

    def execute(self):
        tailers = {}

        def _(e, r):
            plan = self.get_plan(r)
            if not plan.name:
                return
            tailers[plan.name] = plan

        for progress in self.Map(self.get_plan_order(), _, self.ui.echo):
            self.ui.echo("\r[{: >6.2%}] Building plan...".format(progress), nl=False)
        self.ui.echo("")

register(Tail)
