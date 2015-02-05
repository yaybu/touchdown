# Copyright 2011-2015 Isotoma Limited
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

import netaddr
import six

from . import errors, serializers
from .utils import force_str


class Argument(object):

    default = None
    serializer = serializers.Identity()

    def __init__(self, default=None, help=None, **kwargs):
        self.__doc__ = help
        if default is not None:
            self.default = default
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_default(self, instance):
        if callable(self.default):
            return self.default(instance)
        return self.default

    def contribute_to_class(self, cls):
        pass


class Boolean(Argument):

    """ Represents a boolean. "1", "yes", "on" and "true" are all considered
    to be True boolean values. Anything else is False. """

    serializer = serializers.Boolean()

    def clean(self, instance, value):
        if isinstance(value, six.string_types):
            if value.lower() in ("1", "yes", "on", "true"):
                return True
            else:
                return False
        return bool(value)


class String(Argument):

    """ Represents a string. """

    serializer = serializers.String()

    def clean(self, instance, value):
        if value is None:
            return value

        # Automatically cast integers, etc to string
        if not isinstance(value, (six.binary_type, six.text_type)):
            value = str(value)

        return force_str(value)


class Integer(Argument):

    """ Represents an integer argument taken from the source file. This can
    throw an :py:exc:errors.ParseError if the passed in value cannot represent
    a base-10 integer. """

    serializer = serializers.Integer()

    def clean(self, instance, value):
        if not isinstance(value, int):
            try:
                value = int(value)
            except ValueError:
                raise errors.InvalidParameter("%s is not an integer" % value)
        return value


class IPAddress(String):

    serializer = serializers.String()

    def clean(self, instance, value):
        try:
            return netaddr.IPAddress(value)
        except (netaddr.core.AddrFormatError, ValueError):
            raise errors.InvalidParameter("{} is not a valid IP Address")


class IPNetwork(String):

    serializer = serializers.String()

    def clean(self, instance, value):
        try:
            value = netaddr.IPNetwork(value)
        except (netaddr.core.AddrFormatError, ValueError):
            raise errors.InvalidParameter("{} is not a valid IP Address")
        if value != value.cidr:
            raise errors.InvalidParameter("{} looks wrong - did you mean {}?".format(value, value.cdr))
        return value


class Dict(Argument):

    def clean(self, instance, value):
        if not isinstance(value, dict):
            raise errors.InvalidParameter("{} is not a dictionary")
        return value

    def default(self, instance):
        return {}


class List(Argument):

    serializer = None

    def __init__(self, list_of=None, **kwargs):
        super(List, self).__init__(**kwargs)
        self.list_of = list_of
        if not self.serializer:
            self.serializer = serializers.List(
                self.list_of.serializer if self.list_of else serializers.String(),
                skip_empty=True,
            )

    def clean(self, instance, value):
        if not isinstance(value, list):
            raise errors.InvalidParameter("{} is not a list")
        if not self.list_of:
            return value
        result = []
        for entry in value:
            result.append(self.list_of.clean(instance, entry))
        return result

    def default(self, instance):
        return []


class Resource(Argument):

    serializer = serializers.Identifier()

    """
    An argument that represents a resource that we depend on. For example,
    to create an AWS subnet we an AWS VPC to put it in. You might define such a
    subnet as::

        from touchdown.core.resource import Resource
        from touchdown.core import arguments

        class Subnet(Resource):
            cidr_block = argument.CidrBlock()
            vpc = argument.Resource(VPC)
    """

    def __init__(self, resource_class, **kwargs):
        super(Resource, self).__init__(**kwargs)
        self.resource_class = resource_class

    def get_resource_class(self):
        if not isinstance(self.resource_class, (list, tuple)):
            return tuple([self.resource_class] + self.resource_class.__subclasses__())
        return tuple(itertools.chain(
            self.resource_class,
            *[r.__subclasses__() for r in self.resource_class]
        ))

    def get_default(self, instance):
        default = super(Resource, self).get_default(instance)
        if isinstance(default, dict):
            return self.resource_class(instance, **default)
        return default

    def clean(self, instance, value):
        """
        Every time you assign a value to a Resource argument we validate it is
        the correct type. We also mark self as depending on the resource.
        """
        if isinstance(value, dict):
            for resource_class in self.get_resource_class():
                try:
                    value = resource_class(instance, **value)
                    break
                except errors.InvalidParameter:
                    continue
            else:
                raise errors.InvalidParameter("Parameter must be one of {}".format(str(self.get_resource_class())))
        elif hasattr(self.resource_class, "wrap"):
            value = self.resource_class.wrap(instance, value)
        elif not isinstance(value, self.get_resource_class()):
            raise errors.InvalidParameter("Parameter must be a {}".format(self.resource_class))
        instance.add_dependency(value)
        return value

    def contribute_to_class(self, cls):
        """
        If we mark a resource as being assignable to another resource then it
        automatically gains a factory method. Continuing the VPC+Subnet example,
        we can now::

            some_vpc.add_subnet(cidr_block='192.168.0.1/24')

        With this form you don't have to pass the vpc argument (it is done
        implicitly).
        """
        if isinstance(self.resource_class, six.string_types):
            from .resource import ResourceType
            if self.resource_class not in ResourceType.__all_resources__:
                ResourceType.add_callback(self.resource_class, self.contribute_to_class, cls)
                return
            self.resource_class = ResourceType.__all_resources__[self.resource_class]

        argument_name = self.name

        if hasattr(cls, "wrap"):
            return

        if not hasattr(cls, "resource_name"):
            return

        def _(self, **kwargs):
            arguments = {argument_name: self}
            arguments.update(kwargs)
            resource = cls(self, **arguments)
            self.workspace.add_dependency(resource)
            return resource
        setattr(self.resource_class, 'add_%s' % cls.resource_name, _)


class ResourceList(List):

    def __init__(self, resource_class, **kwargs):
        super(ResourceList, self).__init__(
            Resource(resource_class),
            **kwargs
        )

    def contribute_to_class(self, cls):
        resource_class = self.list_of.resource_class
        if isinstance(resource_class, six.string_types):
            from .resource import ResourceType
            if self.resource_class not in ResourceType.__all_resources__:
                ResourceType.add_callback(resource_class, self.contribute_to_class, cls)
                return
            self.list_of.resource_class = ResourceType.__all_resources__[self.resource_class]
        super(ResourceList, self).contribute_to_class(cls)


class Serializer(Argument):

    serializer = serializers.Expression(lambda runner, object: object.render(runner, object))

    def clean(self, instance, value):
        for dep in value.dependencies(instance):
            if dep != instance:
                instance.add_dependency(dep)
        return value
