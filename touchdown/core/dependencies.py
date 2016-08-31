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

from . import errors


class DependencyMap(object):

    ''' If ``tips_first`` is set then the least dependended up nodes will be
    visited first. This is useful if you are deleting all nodes - for example,
    you need to delete subnets before you can delete the VPC they are in.

    If ``tips_first`` is False then the most dependended upon nodes will be
    visited first. This is the default, and is used when creating and apply
    changes - a VPC needs to exist before you can create a subnet in it.
    '''

    def __init__(self, node, tips_first=False):
        self.node = node
        self.tips_first = tips_first
        self.map = {}
        self._prepare()

    def _add_dependency(self, node, dep):
        if self.tips_first:
            self.map.setdefault(dep, set()).add(node)
        else:
            self.map.setdefault(node, set()).add(dep)

    def _prepare(self):
        queue = [self.node]
        visiting = set()
        visited = set()

        while queue:
            node = queue.pop(0)
            visiting.add(node)

            self.map.setdefault(node, set())

            for dep in node.dependencies:
                if dep in visiting:
                    raise errors.CycleError(
                        'Circular reference between %s and %s' % (node, dep)
                    )
                self._add_dependency(node, dep)
                if dep not in visited and dep not in queue:
                    queue.append(dep)

            visiting.remove(node)
            visited.add(node)

    def items(self):
        return self.map.items()

    def get_ready(self):
        ''' Yields resources that are ready to be applied '''
        for node, deps in self.map.items():
            if not deps:
                yield node

    def complete(self, node):
        ''' Marks a node as complete - it's dependents may proceed '''
        del self.map[node]
        for deps in self.map.values():
            deps.difference_update((node,))

    def all(self):
        ''' Visits all remaining nodes in order immediately '''
        while self.map:
            ready = sorted(list(self.get_ready()))
            if not ready:
                return

            for node in ready:
                yield node
                self.complete(node)

    def empty(self):
        return len(self) == 0

    def __len__(self):
        return len(self.map)
