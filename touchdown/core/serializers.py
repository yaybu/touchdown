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

import itertools
import json

from touchdown.core.utils import force_str
from touchdown.core import diff


class FieldNotPresent(Exception):
    pass


class RequiredFieldNotPresent(Exception):
    pass


class Serializer(object):

    def render(self, runner, object):
        raise NotImplementedError(self.render)

    def diff(self, runner, object, value):
        rendered = self.render(runner, object)
        return diff.ValueDiff(value, rendered)

    def dependencies(self, object):
        return frozenset()


class Identity(Serializer):

    def render(self, runner, object):
        return object

    def dependencies(self, object):
        return frozenset()


class SubSerializer(Serializer):

    def render(self, runner, object):
        return object.render(runner, object)

    def dependencies(self, object):
        return frozenset()


class Chain(Serializer):

    def __init__(self, *children, **kwargs):
        self.skip_empty = kwargs.get('skip_empty', False)
        self.children = children

    def render(self, runner, object):
        result = []
        for child in self.children:
            try:
                result.extend(child.render(runner, object))
            except FieldNotPresent:
                pass
        if not len(result) and self.skip_empty:
            raise FieldNotPresent()
        return list(result)

    def dependencies(self, object):
        return frozenset(itertools.chain(*(c.dependencies(object) for c in self.children)))


class Const(Serializer):

    def __init__(self, const):
        self.const = const

    def render(self, runner, object):
        return self.const

    def dependencies(self, object):
        if hasattr(self.const, "add_dependency"):
            return frozenset((self.const, ))
        return frozenset()


class Identifier(Serializer):

    def __init__(self, inner=Identity()):
        self.inner = inner

    def render(self, runner, object):
        if not object:
            raise FieldNotPresent()
        result = runner.get_plan(object).resource_id
        if not result:
            return "pending ({})".format(object)
        return result

    def diff(self, runner, object, value):
        rendered = self.render(runner, object)
        resource = self.inner.render(runner, object)
        if not value or value == rendered:
            return diff.ValueDiff(value, rendered)
        describe = runner.get_plan(resource)
        d = Resource().diff(
            runner,
            resource,
            describe.lookup_version(value),
        )
        d.diffs.insert(0, ("name", diff.ValueDiff(value, rendered)))
        return d

    def dependencies(self, object):
        return self.inner.dependencies(object)


class Property(Serializer):

    def __init__(self, property, inner=Identity()):
        self.property = property
        self.inner = inner

    def render(self, runner, object):
        obj = runner.get_plan(self.inner.render(runner, object)).object
        return obj.get(self.property, "dummy")

    def dependencies(self, object):
        return self.inner.dependencies(object)


class Argument(Serializer):

    def __init__(self, attribute, field=None):
        self.attribute = attribute
        self.field = field

    def get_inner(self, runner, object):
        try:
            result = getattr(object, self.attribute)
        except AttributeError:
            raise FieldNotPresent(self.attribute)
        if not object.meta.fields[self.attribute].present(object):
            if result is None:
                raise FieldNotPresent(self.attribute)
            pass
        return result

    def render(self, runner, object):
        result = self.get_inner(runner, object)
        if isinstance(result, Serializer):
            result = result.render(runner, object)
            if self.field:
                result = self.field.clean_value(object, result)
        else:
            result = object.meta.fields[self.attribute].argument.serializer.render(runner, result)

        return result

    def diff(self, runner, object, value):
        result = self.get_inner(runner, object)
        if isinstance(result, Serializer):
            return result.diff(runner, result, value)
        return object.meta.fields[self.attribute].argument.serializer.diff(runner, result, value)


class Expression(Serializer):

    def __init__(self, callback):
        self.callback = callback

    def render(self, runner, object):
        return self.callback(runner, object)


class Annotation(Serializer):

    """ An annotation node does not change the output, but records some metadata about it """

    def __init__(self, inner):
        self.inner = inner

    def dependencies(self, object):
        return self.inner.dependencies(object)


class Required(Annotation):

    def render(self, runner, object):
        try:
            return self.inner.render(runner, object)
        except FieldNotPresent:
            raise RequiredFieldNotPresent()


class Default(Annotation):

    def __init__(self, inner=Identity(), default=None):
        super(Default, self).__init__(inner)
        self.default = default

    def render(self, runner, object):
        try:
            return self.inner.render(runner, object)
        except FieldNotPresent:
            return self.default


class Formatter(Serializer):

    def __init__(self, inner=Identity()):
        self.inner = inner

    def dependencies(self, object):
        return self.inner.dependencies(object)


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

    def __init__(self, *args, **kwargs):
        self.maybe_empty = kwargs.pop('maybe_empty', False)
        Formatter.__init__(self, *args, **kwargs)

    def render(self, runner, object):
        value = self.inner.render(runner, object)
        if not value:
            if self.maybe_empty:
                return []
            else:
                raise FieldNotPresent()
        return [value]


class CommaSeperatedList(Formatter):
    def render(self, runner, object):
        return ",".join(self.inner.render(runner, object))


class Json(Formatter):
    def render(self, runner, object):
        return json.dumps(self.inner.render(runner, object), sort_keys=True)

    def diff(self, runner, object, value):
        return self.inner.diff(runner, object, json.loads(value))


class Format(Formatter):
    def __init__(self, format_string, inner=Identity()):
        super(Format, self).__init__(inner)
        self.format_string = format_string

    def render(self, runner, object):
        if not object:
            return ""
        if hasattr(object, "resource_name") and not runner.get_plan(object).object:
            return ""
        try:
            return self.format_string.format(self.inner.render(runner, object))
        except:
            return ""


class Dict(Serializer):

    def __init__(self, **kwargs):
        self.kwargs = {}
        for k, v in kwargs.items():
            if not isinstance(v, Serializer):
                v = Const(v)
            self.kwargs[k] = v

    def _render(self, kwargs, runner, object):
        result = dict()
        for key, value in kwargs.items():
            try:
                result[key] = value.render(runner, object)
            except FieldNotPresent:
                continue
        if not len(result):
            raise FieldNotPresent()
        return result

    def render(self, runner, object):
        return self._render(self.kwargs, runner, object)

    def diff(self, runner, object, value):
        d = diff.AttributeDiff()
        rendered = self.render(runner, object)

        for k, v in rendered.items():
            if k not in value:
                d.add(k, diff.ValueDiff("", v))
                continue
            if isinstance(v, dict) and isinstance(value[k], dict):
                d.add(k, Dict(**v).diff(runner, object, value[k]))
                continue
            d.add(k, diff.ValueDiff(v, value[k]))

        for k, v in value.items():
            if k not in rendered:
                d.add(k, diff.ValueDiff(v, ""))

        return d

    def dependencies(self, object):
        return frozenset(itertools.chain(*tuple(c.dependencies(object) for c in self.kwargs.values())))


class Resource(Dict):

    """ Automatically generate a Dict definition by inspect the 'field'
    paramters of a resource """

    def __init__(self, mode="create", group="", **kwargs):
        self.mode = mode
        self.group = group
        super(Resource, self).__init__(**kwargs)

    def should_ignore_field(self, field, value):
        arg = field.argument
        if value is None:
            return True
        if not hasattr(arg, "field"):
            return True
        if arg.field in self.kwargs:
            return True
        if self.mode == "create" and not getattr(arg, "create", True):
            return True
        if self.mode == "update" and not getattr(arg, "update", True):
            return True
        if self.group != getattr(arg, "group", ""):
            return True
        return False

    def render(self, runner, object):
        if hasattr(object, "get_serializer"):
            return object.get_serializer(runner, **self.kwargs).render(runner, object)

        kwargs = dict(self.kwargs)

        if not self.group:
            for name, serializer in getattr(object, "extra_serializers", {}).items():
                kwargs[name] = serializer

        for field in object.meta.iter_fields_in_order():
            value = field.get_value(object)
            if self.should_ignore_field(field, value):
                continue

            kwargs[field.argument.field] = Argument(field.name, field)

        return self._render(kwargs, runner, object)

    def diff(self, runner, obj, value):
        d = diff.AttributeDiff()
        for field in obj.meta.iter_fields_in_order():
            name = field.name
            arg = field.argument
            if not field.present(obj):
                continue
            if not getattr(arg, "field", ""):
                continue
            if not getattr(arg, "update", True):
                continue
            if getattr(arg, "group", "") != self.group:
                continue
            if not getattr(obj, name) and arg.field not in value:
                continue

            # If a field is present in the remote, then diff against that
            # If a field is not present in the remote, diff against the default
            if arg.field in value:
                remote_val = value[arg.field]
            else:
                remote_val = arg.get_default(obj)

            try:
                d.add(field.name, Argument(field.name, field).diff(runner, obj, remote_val))
            except FieldNotPresent:
                continue

        return d

    def dependencies(self, object):
        raise NotImplementedError(self.dependencies, object)


class List(Serializer):

    def __init__(self, child=Identity(), skip_empty=False):
        self.child = child
        self.skip_empty = skip_empty

    def render(self, runner, object):
        result = []
        for row in object:
            try:
                result.append(self.child.render(runner, row))
            except FieldNotPresent:
                pass
        if not result and self.skip_empty:
            raise FieldNotPresent()
        return list(result)

    def diff(self, runner, object, value):
        for renderable, value in itertools.izip_longest(object, value):
            if not renderable:
                return diff.ValueDiff("", "ITEM REMOVED")
            elif not value:
                return diff.ValueDiff("ITEM ADDED", "")
            d = self.child.diff(runner, renderable, value)
            if not d.matches():
                return d
        return diff.ValueDiff("", "")

    def dependencies(self, object):
        return frozenset(self.child.dependencies(object))


class Context(Serializer):

    def __init__(self, serializer, inner):
        if not isinstance(serializer, Serializer):
            serializer = Const(serializer)
        self.serializer = serializer
        self.inner = inner

    def render(self, runner, object):
        object = self.serializer.render(runner, object)
        return self.inner.render(runner, object)

    def diff(self, runner, object, value):
        object = self.serializer.render(runner, object)
        return self.inner.diff(runner, object, value)

    def dependencies(self, object):
        return self.inner.dependencies(object).union(self.serializer.dependencies(object))


def maybe(val):
    if not isinstance(val, Serializer):
        return Const(val)
    return val
