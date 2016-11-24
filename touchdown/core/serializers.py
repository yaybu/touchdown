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

import jmespath

from six.moves import zip_longest
from touchdown.core import diff, errors
from touchdown.core.utils import force_bytes, force_str


class FieldNotPresent(Exception):
    pass


class RequiredFieldNotPresent(Exception):
    pass


class Pending(object):
    ''' A render can return a Pending if it is rendered while in the pending state
       eq and nonzero are safety check to ensure it's not used anywhere
    '''

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return False

    def __nonzero__(self):
        return True

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return '(pending {})'.format(self.value)


class Serializer(object):

    def render(self, runner, object):
        ''' turn incoming into 'json' for botocore '''
        raise NotImplementedError(self.render)

    def diff(self, runner, object, value):
        ''' takes a resource and some botocore 'stuff'. returns the differences '''
        rendered = self.render(runner, object)
        return diff.ValueDiff(value, rendered)

    def pending(self, runner, obj):
        ''' given something to serialize, do I know enough to serialize it yet '''
        return False

    def dependencies(self, object):
        ''' given something to serialize what other things do I need in order to serialize it '''
        return frozenset()


class Identity(Serializer):

    def render(self, runner, object):
        return object

    def pending(self, runner, object):
        return isinstance(object, Pending)

    def dependencies(self, object):
        return frozenset()


class SubSerializer(Serializer):

    def render(self, runner, object):
        return object.render(runner, object)

    def pending(self, runner, object):
        return object.pending(runner, object)

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

    def pending(self, runner, object):
        return any(itertools.chain(*(c.pending(runner, object) for c in self.children)))

    def dependencies(self, object):
        return frozenset(itertools.chain(*(c.dependencies(object) for c in self.children)))


class Const(Serializer):

    def __init__(self, const):
        self.const = const

    def render(self, runner, object):
        return self.const

    def pending(self, runner, object):
        return isinstance(object, Pending)

    def dependencies(self, object):
        if hasattr(self.const, 'add_dependency'):  # if is a Resource
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
            return Pending(object)
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
            describe.get_object_by_id(value),
        )
        d.diffs.insert(0, ('name', diff.ValueDiff(value, rendered)))
        return d

    def pending(self, runner, object):
        return self.inner.pending(runner, object)

    def dependencies(self, object):
        return self.inner.dependencies(object)


class Property(Serializer):
    ''' an output from a botocore action
        e.g. describe queue returns queue_url'''

    def __init__(self, property, inner=Identity()):
        self.selector = property
        self.property = jmespath.compile(property)
        self.inner = inner

    def render(self, runner, object):
        target = self.inner.render(runner, object)
        target_plan = runner.get_plan(target)
        if not target_plan.resource_id:
            return Pending(target)
        result = self.property.search(target_plan.object)
        if not result:
            raise errors.Error('{} not available'.format(self.selector))
        return result

    def pending(self, runner, object):
        if self.inner.pending(runner, object):
            return True
        target = self.inner.render(runner, object)
        target_plan = runner.get_plan(target)
        if not target_plan.resource_id:
            return True
        return False

    def dependencies(self, object):
        return self.inner.dependencies(object)


class Argument(Serializer):
    ''' for retrieving an argument from a resource object
        i.e. rather than acting on this resource act on a field of this resource
    '''

    def __init__(self, attribute, field=None):
        self.attribute = attribute
        self.field = field

    def get_inner(self, runner, object):
        try:
            result = getattr(object, self.attribute)
        except AttributeError:
            raise
            raise FieldNotPresent(self.attribute)
        if not object.meta.fields[self.attribute].present(object):
            if result is None:
                raise FieldNotPresent(self.attribute)
            pass
        return result

    def render(self, runner, object):
        try:
            result = self.get_inner(runner, object)
        except FieldNotPresent:
            if self.field.argument.empty_serializer:
                return self.field.argument.empty_serializer.render(runner, object)
            raise

        if isinstance(result, Serializer):
            result = result.render(runner, object)
            if self.field:
                result = self.field.clean_value(object, result)

        return object.meta.fields[self.attribute].argument.serializer.render(runner, result)

    def diff(self, runner, object, value):
        try:
            result = self.get_inner(runner, object)
        except FieldNotPresent:
            if self.field.argument.empty_serializer:
                return self.field.argument.empty_serializer.diff(runner, object, value)
            raise

        if isinstance(result, Serializer):
            return result.diff(runner, result, value)
        return object.meta.fields[self.attribute].argument.serializer.diff(runner, result, value)

    def pending(self, runner, object):
        try:
            inner = self.get_inner(runner, object)
        except FieldNotPresent:
            if self.field.argument.empty_serializer:
                return self.field.argument.empty_serializer.pending(runner, object)
            return False

        if maybe(inner).pending(runner, object):
            return True

        return object.meta.fields[self.attribute].argument.serializer.pending(runner, inner)


class Expression(Serializer):

    def __init__(self, callback):
        self.callback = callback

    def render(self, runner, object):
        if isinstance(object, Pending):
            return object
        return self.callback(runner, object)

    def pending(self, runner, object):
        return isinstance(object, Pending)


class Annotation(Serializer):

    ''' An annotation node does not change the output, but records some metadata about it '''

    def __init__(self, inner):
        self.inner = inner

    def pending(self, runner, object):
        return self.inner.pending(runner, object)

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
    ''' abc '''

    def __init__(self, inner=Identity()):
        self.inner = inner

    def pending(self, runner, object):
        return self.inner.pending(runner, object)

    def dependencies(self, object):
        return self.inner.dependencies(object)


class Boolean(Formatter):

    def __init__(self, inner=Identity(), on_true=True, on_false=False):
        super(Boolean, self).__init__(inner)
        self.on_true = on_true
        self.on_false = on_false

    def render(self, runner, object):
        return self.on_true if self.inner.render(runner, object) else self.on_false


class String(Formatter):

    def render(self, runner, object):
        if object is None:
            return None

        try:
            return force_str(self.inner.render(runner, object))
        except ValueError:
            return str(self.inner.render(runner, object))

    def diff(self, runner, object, value):
        return super(String, self).diff(runner, object, None if value is None else str(value))


class Bytes(Formatter):

    def render(self, runner, object):
        if object is None:
            return None

        try:
            return force_bytes(self.inner.render(runner, object))
        except ValueError:
            return str(self.inner.render(runner, object))

    def diff(self, runner, object, value):
        return super(Bytes, self).diff(runner, object, None if value is None else str(value))


class Integer(Formatter):
    def render(self, runner, object):
        return int(self.inner.render(runner, object))


class ListOfOne(Formatter):
    ''' list that can only have one entry - thanks amazon '''

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

    def diff(self, runner, object, value):
        return self.inner.diff(runner, object, value[0])


class CommaSeperatedList(Formatter):
    def render(self, runner, object):
        return ','.join(self.inner.render(runner, object))

    def diff(self, runner, object, value):
        v = value.split(',') if value else []
        return self.inner.diff(runner, object, v)


class Json(Formatter):
    def render(self, runner, object):
        return json.dumps(self.inner.render(runner, object), sort_keys=True)

    def diff(self, runner, object, value):
        value = json.loads(value) if value else {}
        return self.inner.diff(runner, object, value)


class Append(Formatter):

    def __init__(self, post_string, inner=Identity()):
        super(Append, self).__init__(inner)
        self.post_string = post_string

    def render(self, runner, object):
        inner = self.inner.render(runner, object)
        if isinstance(inner, Pending):
            return inner
        return '{}{}'.format(inner, self.post_string)


class Format(Formatter):
    def __init__(self, format_string, inner=Identity()):
        super(Format, self).__init__(inner)
        self.format_string = format_string

    def render(self, runner, object):
        if not object:
            return ''
        if hasattr(object, 'resource_name') and not runner.get_plan(object).object:
            return ''
        try:
            return self.format_string.format(self.inner.render(runner, object))
        except:
            return ''


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
        rendered = self._render(self.kwargs, runner, object)

        for k, v in rendered.items():
            if not value or k not in value:
                d.add(k, diff.ValueDiff(None, v))
                continue
            if isinstance(v, dict) and isinstance(value[k], dict):
                d.add(k, Dict(**v).diff(runner, object, value[k]))
                continue
            d.add(k, diff.ValueDiff(value[k], v))

        if value:
            for k, v in value.items():
                if k not in rendered:
                    d.add(k, diff.ValueDiff(v, None))

        return d

    def pending(self, runner, object):
        return any(v.pending(runner, v) for v in self.kwargs.values())

    def dependencies(self, object):
        return frozenset(itertools.chain(*tuple(c.dependencies(object) for c in self.kwargs.values())))


class Map(Dict):

    def render(self, runner, object):
        result = dict()
        for key, value in object.items():
            try:
                result[key] = maybe(value).render(runner, object)
            except FieldNotPresent:
                continue
        if not len(result):
            raise FieldNotPresent()
        return result

    def diff(self, runner, object, value):
        d = diff.AttributeDiff()

        for k, v in object.items():
            if isinstance(v, dict) and isinstance(value.get(k, None), dict):
                d.add(k, Dict(**v).diff(runner, object, value[k]))
                continue
            d.add(k, maybe(v).diff(runner, v, value.get(k, None)))

        for k, v in value.items():
            if k not in object:
                d.add(k, diff.ValueDiff(v, None))

        return d

    def pending(self, runner, object):
        return any(maybe(v).pending(runner, v) for v in object.values())

    def dependencies(self, object):
        return frozenset(itertools.chain(*tuple(maybe(c).dependencies(object) for c in object.values())))


class Resource(Dict):

    ''' Automatically generate a Dict definition by inspect the 'field'
    paramters of a resource '''

    def __init__(self, mode='create', group='', **kwargs):
        self.mode = mode
        self.group = group
        super(Resource, self).__init__(**kwargs)

    def should_ignore_field(self, object, field, value):
        arg = field.argument
        if not hasattr(arg, 'field'):
            return True
        if not arg.empty_serializer and not field.present(object):
            if value is None:
                return True
        if arg.field in self.kwargs:
            return True
        if self.mode == 'create' and not getattr(arg, 'create', True):
            return True
        if self.mode == 'update' and not getattr(arg, 'update', True):
            return True
        if self.group != getattr(arg, 'group', ''):
            return True
        return False

    def render(self, runner, object):
        if hasattr(object, 'get_serializer'):
            return object.get_serializer(runner, **self.kwargs).render(runner, object)

        kwargs = dict(self.kwargs)

        if not self.group:
            for name, serializer in getattr(object, 'extra_serializers', {}).items():
                kwargs[name] = serializer

        for field in object.meta.iter_fields_in_order():
            value = field.get_value(object)
            if self.should_ignore_field(object, field, value):
                continue
            kwargs[field.argument.field] = Argument(field.name, field)

        return self._render(kwargs, runner, object)

    def diff(self, runner, obj, value):
        d = diff.AttributeDiff()

        if not obj:
            return diff.ItemRemoved(value)

        for field in obj.meta.iter_fields_in_order():
            arg = field.argument
            if not field.present(obj):
                continue
            if not getattr(arg, 'field', ''):
                continue
            if not getattr(arg, 'update', True):
                continue
            if getattr(arg, 'group', '') != self.group:
                continue

            # If a field is present in the remote, then diff against that
            # If a field is not present in the remote, diff against the default
            if value and arg.field in value:
                remote_val = value[arg.field]
            else:
                remote_val = None

            try:
                d.add(field.name, Argument(field.name, field).diff(runner, obj, remote_val))
            except FieldNotPresent:
                continue

        return d

    def pending(self, runner, object):
        for field in object.meta.iter_fields_in_order():
            value = field.get_value(object)
            if self.should_ignore_field(object, field, value):
                continue
            if Argument(field.name, field).pending(runner, object):
                return True
        return False

    def dependencies(self, object):
        return set()


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

    def _find_intersections(self, runner, old, new):
        matches = {}
        # FIXME: This is incredibly inefficient, which is why we only take this
        # code path for small values of `value` or `object`
        for i, o in enumerate(old):
            for j, n in enumerate(new):
                if self.child.diff(runner, n, o).matches():
                    matches.setdefault(j, []).append(i)
        return matches

    def _find_longest_intersection(self, old, new, intersections):
        longest_intersections = {}
        length = start_new = start_old = 0
        for i, v in enumerate(new):
            _longest_intersections = {}
            for j in intersections.get(i, []):
                _longest_intersections[j] = (j and longest_intersections.get(j - 1, 0)) + 1
                if _longest_intersections[j] > length:
                    length = _longest_intersections[j]
                    start_old = j - length + 1
                    start_new = i - length + 1
            longest_intersections = _longest_intersections
        return length, start_old, start_new

    def _walk_intersections(self, runner, old, new):
        length, start_old, start_new = self._find_longest_intersection(
            old,
            new,
            self._find_intersections(runner, old, new),
        )

        if length == 0:
            # No intersections between begin and end...
            return itertools.chain(
                [('-', old)] if old else [],
                [('+', new)] if new else [],
            )
        else:
            return itertools.chain(
                self._walk_intersections(runner, old[:start_old], new[:start_new]),
                [('=', new[start_new:start_new+length])],
                self._walk_intersections(runner, old[start_old + length:], new[start_new + length:]),
            )

    def diff_slow(self, runner, object, value):
        diffs = diff.ListDiff()
        idx = 0
        pending = []
        intersections = itertools.chain(
            self._walk_intersections(runner, value, object),
            [('*', [])],
        )
        for op, vals in intersections:
            if op == '-':
                pending = vals
            elif op == '+':
                for i, (old, new) in enumerate(zip_longest(pending, vals), idx):
                    diffs.add(i, self.child.diff(runner, new, old))
                pending = []
            elif pending and op in ('=', '*'):
                for i, old in enumerate(pending, idx):
                    diffs.add(i, self.child.diff(runner, None, old))
                pending = []

            idx += len(vals)
        return diffs

    def diff_stupid(self, runner, object, value):
        diffs = diff.ListDiff()
        for i, (renderable, v) in enumerate(zip_longest(object or [], value or [])):
            diffs.add(i, self.child.diff(runner, renderable, v))
        return diffs

    def diff(self, runner, object, value):
        if object and value and len(object) < 50 and len(value) < 50:
            return self.diff_slow(runner, object, value)
        return self.diff_stupid(runner, object, value)

    def pending(self, runner, object):
        for item in object:
            if self.child.pending(runner, item):
                return True
        return False

    def dependencies(self, object):
        return frozenset(self.child.dependencies(object))


class Context(Serializer):
    ''' new way of doing inner (Identity) '''

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

    def pending(self, runner, object):
        if self.serializer.pending(runner, object):
            return True
        object = self.serializer.render(runner, object)
        return self.inner.pending(runner, object)

    def dependencies(self, object):
        return self.inner.dependencies(object).union(self.serializer.dependencies(object))


def maybe(val):
    if not isinstance(val, Serializer):
        return Const(val)
    return val
