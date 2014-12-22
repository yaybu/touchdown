# Copyright 2014 Isotoma Limited
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

import logging
import six

from . import errors
from .argument import Argument, PolicyArgument

logger = logging.getLogger(__name__)


class ResourceType(type):

    def __new__(meta, class_name, bases, new_attrs):
        for sub in new_attrs.get("subresources", []):
            def _(self, **kwargs):
                r = sub(self.root, **kwargs)
                self.root.add_dependency(r)
                if self != self.root:
                    r.add_dependency(self)
                return r
            new_attrs['add_%s' % sub.resource_name] = _

        cls = type.__new__(meta, class_name, bases, new_attrs)

        cls.__args__ = {}

        for b in bases:
            if hasattr(b, "__args__"):
                cls.__args__.update(b.__args__)

        for key, value in new_attrs.items():
            if isinstance(value, Argument):
                cls.__args__[key] = value

        return cls


class Resource(six.with_metaclass(ResourceType)):

    default_policy = None
    policies = {}

    policy = PolicyArgument()

    def __init__(self, root, **kwargs):
        self.root = root
        self.dependencies = set()
        for key, value in kwargs.items():
            if key not in self.__args__:
                raise errors.Error("'%s' is not a valid option" % (key, ))
            setattr(self, key, value)

    def add_dependency(self, dependency):
        self.dependencies.add(dependency)

    def __str__(self):
        return self.resource_name
