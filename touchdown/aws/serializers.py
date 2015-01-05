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

from touchdown.core import argument
from touchdown.core.utils import force_str


class hd(dict):

    def __hash__(self):
        return hash(frozenset(self.items()))


class FieldNotPresent(Exception):
    pass


class RequiredFieldNotPresent(Exception):
    pass


class Serializer(object):

    def render(self, runner, object):
        raise NotImplementedError(self.render)


class Identity(Serializer):

    def render(self, runner, object):
        return object


class Const(Serializer):

    def __init__(self, const):
        self.const = const

    def render(self, runner, object):
        return self.const


class Identifier(Serializer):

    def __init__(self, inner=Identity()):
        self.inner = inner

    def render(self, runner, object):
        result = runner.get_target(self.inner.render(runner, object)).resource_id
        if not result:
            return "pending ({})".format(object)
        return result


class Property(Serializer):

    def __init__(self, property, inner=Identity()):
        self.property = property
        self.inner = inner

    def render(self, runner, object):
        return runner.get_target(self.inner.render(runner, object)).object.get(self.property, "dummy")


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

    def __init__(self, inner=Identity()):
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


class ListOfOne(Formatter):
    def render(self, runner, object):
        return [self.inner.render(runner, object)]


class CommaSeperatedList(Formatter):
    def render(self, runner, object):
        return ",".join(self.inner.render(runner, object))


class Dict(Serializer):

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def render(self, runner, object):
        result = hd()
        for key, value in self.kwargs.items():
            try:
                result[key] = value.render(runner, object)
            except FieldNotPresent:
                continue
        return result


class Resource(Dict):

    """ Automatically generate a Dict definition by inspect the aws_field
    paramters of a resource """

    def __init__(self, mode="create"):
        self.mode = mode
        self.kwargs = {}

    def render(self, runner, object):
        for argument_name, arg in object.arguments:
            if not arg.present(object):
                continue
            if not hasattr(arg, "aws_field"):
                continue
            if self.mode == "create" and not getattr(arg, "aws_create", True):
                continue
            if self.mode == "update" and not getattr(arg, "aws_update", True):
                continue

            value = Argument(argument_name)
            if hasattr(arg, "aws_serializer"):
                value = Context(value, arg.aws_serializer)
            if isinstance(arg, argument.Resource):
                value = Identifier(inner=value)
            elif isinstance(arg, argument.ResourceList):
                value = Context(value, List(Identifier()))
            self.kwargs[arg.aws_field] = value

        return super(Resource, self).render(runner, object)


class List(Serializer):

    def __init__(self, child=Identity(), skip_empty=False):
        self.child = child
        self.skip_empty = skip_empty

    def render(self, runner, object):
        result = []
        for row in object:
            result.append(self.child.render(runner, row))
        if not result and self.skip_empty:
            raise FieldNotPresent()
        return tuple(result)


class Context(Serializer):

    def __init__(self, serializer, inner):
        self.serializer = serializer
        self.inner = inner

    def render(self, runner, object):
        object = self.serializer.render(runner, object)
        return self.inner.render(runner, object)
