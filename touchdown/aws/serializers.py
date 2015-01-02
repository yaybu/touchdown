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

from touchdown.core import errors, target
from touchdown.core.utils import force_str


class FieldNotPresent(Exception):
    pass


class RequiredFieldNotPresent(Exception):
    pass


class Serializer(object):

    def render(self, runner, object):
        raise NotImplementedError(self.render)


class Const(Serializer):

    def __init__(self, const):
        self.const = const

    def render(self, runner, object):
        return self.const


class Identifier(Serializer):

    def render(self, runner, object):
        result = self.runner.get_target(object).resource_id
        if not result:
            return "pending ({})".format(object)


class Argument(Serializer):

    def __init__(self, attribute):
        self.attribute = attribute

    def render(self, runner, object):
        if not object.__args__[self.attribute].present(object):
            raise FieldNotPresent(self.attribute)
        return getattr(object, self.attribute)


class Expression(Serializer):

    def __init__(self, callback):
        self.callback = callback

    def render(self, runner, object):
        return self.callback(runner, object)


class Annotation(Serializer):

    """ An annotation node does not change the output, but records some metadata about it """

    def __init__(self, inner):
        self.inner = inner


class Required(Annotation):

    def render(self, runner, object):
        try:
            return self.inner.render(runner, object)
        except FieldNotPresent:
            raise RequiredFieldNotPresent()


class Formatter(Serializer):

    def __init__(self, inner):
        self.inner = inner


class Boolean(Formatter):

    def render(self, runner, object):
        return True if self.inner.render(runner, object) else False


class String(Formatter):
    def render(self, runner, object):
        try:
            return force_str(self.inner.render(runner, object))
        except ValueError:
            return str(self.inner.render(runner, object))


class Integer(Formatter):
    def render(self, runner, object):
        return int(self.inner.render(runner, object))


class Dict(Serializer):

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def render(self, runner, object):
        result = {}
        for key, value in self.kwargs.items():
            try:
                result[key] = value.render(runner, object)
            except NotPresent:
                continue
        return result


class List(Serializer):

    def __init__(self, inner):
        self.inner = inner

    def render(self, runner, object):
        result = []
        for row in object:
            result.append(self.inner.render(runner, row))
        return result
