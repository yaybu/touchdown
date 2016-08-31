# Copyright 2016 Isotoma Limited
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

from touchdown.core.dependencies import DependencyMap


class DoesNotExist(Exception):
    pass


class MultipleResourcesFound(Exception):
    pass


class Traversal(object):

    def __init__(self, root, parent):
        self.root = root
        self.parent = parent
        self._cache = None

    def resolve(self):
        if self._cache is None:
            self._cache = list(self._get_matches())
        return self._cache

    def iterator(self):
        for result in self.resolve():
            yield result

    def get(self):
        if len(self) == 0:
            raise DoesNotExist()
        if len(self) > 1:
            raise MultipleResourcesFound()
        return list(self)[0]

    def outgoing(self, expression):
        return Outgoing(self.root, self, expression)

    def adjacent_incoming(self):
        return AdjacentIncoming(self.root, self)

    def adjacent_outgoing(self):
        return AdjacentOutgoing(self.root, self)

    def __len__(self):
        return len(self.resolve())

    def __iter__(self):
        return self.iterator()


class Outgoing(Traversal):

    def __init__(self, root, parent, expression):
        super(Outgoing, self).__init__(root, parent)
        self.expression = expression

    def matches(self, node):
        ''' Returns True if a given node matches a selection expression '''
        if ':' in self.expression:
            resource_class, resource_name = self.expression.split(':', 1)
        else:
            resource_class, resource_name = '', self.expression

        if resource_class and resource_class != node.resource_name:
            return False

        if resource_name and resource_name != getattr(node, 'name', None):
            return False

        return True

    def _get_matches(self):
        queue = list(self.parent.resolve())
        visited = set()
        while queue:
            node = queue.pop(0)
            for dep in self.root.backward.map[node]:
                if dep not in visited and dep not in queue:
                    queue.append(dep)
            if self.matches(node):
                yield node
            visited.add(node)


class AdjacentIncoming(Traversal):

    def _get_matches(self):
        for node in self.parent.resolve():
            for incoming in self.root.backward.map[node]:
                yield incoming


class AdjacentOutgoing(Traversal):

    def _get_matches(self):
        for node in self.parent.resolve():
            for incoming in self.root.forward.map[node]:
                yield incoming


class Walker(object):

    def __init__(self, workspace):
        self.workspace = workspace
        self.forward = DependencyMap(workspace)
        self.backward = DependencyMap(workspace, True)

    def starting_at(self, *nodes):
        retval = Traversal(self, None)
        retval._cache = set(nodes)
        return retval

    def most_depended(self):
        matches = set()
        for node, dependencies in self.backward.items():
            if len(dependencies) > 0:
                continue
            matches.add(node)
        retval = Traversal(self, None)
        retval._cache = matches
        return retval

    def least_depended(self):
        matches = set()
        for node, dependencies in self.forward.items():
            if len(dependencies) > 0:
                continue
            matches.add(node)
        retval = Traversal(self, None)
        retval._cache = matches
        return retval

    def find(self, selectors):
        expr = self.least_depended()
        for selector in selectors:
            expr = expr.outgoing(selector)
        return expr
