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

from touchdown.core.goals import Goal, register


class Tail(Goal):

    name = "tail"

    def get_plan_class(self, resource):
        plan_class = resource.meta.get_plan("tail")
        if not plan_class:
            plan_class = resource.meta.get_plan("null")
        return plan_class

    def execute(self):
        tailers = {}

        def _(e, r):
            p = self.get_plan(r)
            if p.name == "tail":
                tailers[p.resource.name] = p

        for progress in self.Map(self.get_plan_order(), _, self.ui.echo):
            self.ui.echo("\r[{: >6.2%}] Building plan...".format(progress), nl=False)
        self.ui.echo("")

        tailers["application.log"].tail("5m", None, True)

register(Tail)
