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


class Dot(Goal):

    ''' Generate a dot graph of all resources and their interconnections '''

    name = 'dot'
    mutator = False

    def get_plan_class(self, resource):
        return plan.NullPlan

    def get_digraph(self):
        graph = ['digraph ast {']

        for node, deps in self.get_plan_order().items():
            if node.dot_ignore:
                continue
            graph.append('{} [label="{}"];'.format(id(node), node))
            for dep in deps:
                if dep.dot_ignore:
                    continue
                graph.append('{} -> {};'.format(id(node), id(dep)))

        graph.append('}')
        return '\n'.join(graph)

    def execute(self):
        self.ui.echo(self.get_digraph())

register(Dot)
