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

from . import argument, errors, serializers

logger = logging.getLogger(__name__)
marker = object()


class Field(object):

    def __init__(self, name, argument):
        self.name = name
        self.argument = argument
        self.__doc__ = self.argument.__doc__

    def present(self, instance):
        return self.argument.present(instance)

    def get_value(self, instance):
        retval = instance._values.get(self.name, marker)
        if retval is marker:
            return self.argument.get_default(instance)
        return retval

    def delete_value(self, instance):
        if self.name in instance._values:
            del instance._values[self.name]

    def clean_value(self, instance, value):
        try:
            value = self.argument.clean(instance, value)
            if hasattr(instance, 'clean_{}'.format(self.name)):
                value = getattr(instance, 'clean_{}'.format(self.name))(value)
        except errors.InvalidParameter as e:
            raise errors.InvalidParameter('{}: {}'.format(self.name, e.args[0]))
        return value

    def __set__(self, instance, value):
        if value is None:
            self.delete_value(instance)
            return

        value = self.argument.adapt(value)
        if isinstance(value, serializers.Serializer):
            for dep in value.dependencies(instance):
                if dep != instance:
                    instance.add_dependency(dep)
        else:
            value = self.clean_value(instance, value)
            for dep in self.argument.serializer.dependencies(value):
                if dep != instance:
                    instance.add_dependency(dep)
        instance._values[self.name] = value

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self.get_value(instance)


class Meta(object):

    def __init__(self):
        self.plans = {}
        self.fields = {}
        self.field_order = []

    def get_plan(self, plan):
        for cls in self.mro:
            if hasattr(cls, 'meta') and plan in cls.meta.plans:
                return cls.meta.plans[plan]

    def iter_fields_in_order(self):
        for name in self.field_order:
            yield self.fields[name]


class ResourceType(type):

    __all_resources__ = {}
    __lazy_lookups__ = {}

    def __new__(meta_cls, class_name, bases, new_attrs):
        meta = new_attrs['meta'] = Meta()

        # FIXME: What order to process the bases in?
        for base in bases:
            if hasattr(base, 'meta') and isinstance(base.meta, Meta):
                meta.fields.update(base.meta.fields)
                meta.field_order.extend(base.meta.field_order)

        # A resource can set its own field_order. An example of when this is
        # useful is the AWS subnet. We want to validate that its cidr_block
        # fits inside the cidr_block of its parent vpc. So the vpc must always
        # be processed first. This guarantee can't be made with kwargs on
        # cpython.
        if 'field_order' in new_attrs:
            meta.field_order.extend(new_attrs['field_order'])
            del new_attrs['field_order']

        # Replace all Argument instances with Field instances. The Field type
        # handles the 'clean' stage of input processing and the storage of
        # data passed in.
        for name, value in new_attrs.items():
            if isinstance(value, argument.Argument):
                field = new_attrs[name] = Field(name, value)
                meta.fields[name] = field
                meta.field_order.append(name)
                value.name = name

        # De-duplicate the field_order list
        field_order = []
        for field in meta.field_order:
            if field not in field_order:
                field_order.append(field)
        meta.field_order = field_order

        # Actually build a class
        cls = type.__new__(meta_cls, class_name, bases, new_attrs)
        cls.meta.mro = cls.mro()

        # Allow fields to contribute to the class...
        for field in cls.meta.iter_fields_in_order():
            field.argument.contribute_to_class(cls)

        # Fire any signals.
        name = '.'.join((cls.__module__, cls.__name__))
        meta_cls.__all_resources__[name] = cls

        for callable, args, kwargs in meta_cls.__lazy_lookups__.get(name, []):
            callable(*args, **kwargs)

        return cls

    @classmethod
    def add_callback(cls, name, callback, *args, **kwargs):
        cls.__lazy_lookups__.setdefault(name, []).append((callback, args, kwargs))


class Resource(six.with_metaclass(ResourceType)):

    dot_ignore = False
    default_plan = None

    ensure = argument.List(argument.String())

    def __init__(self, parent, **kwargs):
        self._values = {}
        self.dependencies = set()
        self.parent = parent

        params = self.clean(kwargs)
        for field in self.meta.iter_fields_in_order():
            if field.name in params:
                setattr(self, field.name, params[field.name])

    @classmethod
    def clean(cls, value):
        if not isinstance(value, dict):
            raise errors.InvalidParameter(
                '{!r} cannot be adapted into a {}'.format(value, cls.resource_name)
            )

        params = {}
        compound_params = {}
        for key, subvalue in value.items():
            if '__' in key:
                key, subkey = key.split('__', 1)
                compound_params.setdefault(key, {})[subkey] = subvalue
                continue
            params[key] = subvalue

        for key, val in compound_params.items():
            if key in params:
                raise errors.InvalidParameter(
                    'Cannot set "{}" and "{}__{}"'.format(
                        key,
                        key,
                        next(iter(val.keys())),
                    )
                )
            params[key] = val

        for key in params.keys():
            if key not in cls.meta.fields:
                raise errors.InvalidParameter(
                    '{!r} is not a valid option for a {}'.format(key, cls.resource_name)
                )

        return params

    def identifier(self):
        ''' Returns a serializer that renders the identity of the resource, e.g. 'ami-123456' '''
        return serializers.Context(
            serializers.Const(self),
            serializers.Identifier(),
        )

    def get_property(self, property_name):
        ''' Returns a serializer that renders a property fetched by describing a remote resource '''
        return serializers.Property(
            property_name,
            serializers.Const(self),
        )

    def serializer_with_kwargs(self, **kwargs):
        return serializers.Context(
            serializers.Const(self),
            serializers.Resource(**kwargs),
        )

    def diff(self, runner, value, **kwargs):
        return serializers.Resource(**kwargs).diff(
            runner,
            self,
            value
        )

    @property
    def arguments(self):
        return list((name, field.argument) for (name, field) in self.meta.iter_fields_in_order())

    @property
    def workspace(self):
        if self.parent:
            return self.parent.workspace

    def add_dependency(self, dependency):
        if self.workspace != dependency:
            self.dependencies.add(dependency)

    def __str__(self):
        if hasattr(self, 'name'):
            return '{} \'{}\''.format(self.resource_name, self.name)
        return self.resource_name

    def __lt__(self, other):
        return str(self) < str(other)
