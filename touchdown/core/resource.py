# Copyright 2011-2014 Isotoma Limited
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
from .argument import Argument, List

logger = logging.getLogger(__name__)


class ResourceType(type):

    __all_resources__ = {}
    __lazy_lookups__ = {}

    def __new__(meta, class_name, bases, new_attrs):
        new_attrs['plans'] = {}

        cls = type.__new__(meta, class_name, bases, new_attrs)

        cls.__args__ = {}
        for key in dir(cls):
            value = getattr(cls, key)
            if isinstance(value, Argument):
                cls.__args__[key] = value
                value.argument_name = key
                value.contribute_to_class(cls)

        name = ".".join((cls.__module__, cls.__name__))
        meta.__all_resources__[name] = cls

        for callable, args, kwargs in meta.__lazy_lookups__.get(name, []):
            callable(*args, **kwargs)

        return cls

    @classmethod
    def add_callback(cls, name, callback, *args, **kwargs):
        cls.__lazy_lookups__.setdefault(name, []).append((callback, args, kwargs))


class Resource(six.with_metaclass(ResourceType)):

    dot_ignore = False
    default_plan = None

    policies = List()

    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.dependencies = set()
        for key, value in kwargs.items():
            if key not in self.__args__:
                raise errors.InvalidParameter("'%s' is not a valid option" % (key, ))
            setattr(self, key, value)

    @property
    def arguments(self):
        return list(self.__args__.items())

    @property
    def workspace(self):
        if self.parent:
            return self.parent.workspace

    def add_dependency(self, dependency):
        if self.workspace != dependency:
            self.dependencies.add(dependency)

    def __str__(self):
        if hasattr(self, "name"):
            return "{} '{}'".format(self.resource_name, self.name)
        return self.resource_name
