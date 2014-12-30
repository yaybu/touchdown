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

import six

import netaddr

from . import errors, target
from .utils import force_str


class Argument(object):

    """ Stores the argument value on the instance object. It's a bit fugly,
    neater ways of doing this that do not involve passing extra arguments to
    Argument are welcome. """

    argument_id = 0
    default = None

    def __init__(self, default=None, help=None, **kwargs):
        self.__doc__ = help
        if default:
            self.default = default
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.arg_id = "argument_%d" % Argument.argument_id
        Argument.argument_id += 1

    def __get__(self, instance, owner):
        if instance is None:
            return self
        elif self.present(instance):
            return getattr(instance, self.arg_id)
        elif callable(self.default):
            return self.default(instance)
        else:
            return self.default

    def present(self, instance):
        return hasattr(instance, self.arg_id)

    def contribute_to_class(self, cls):
        pass

    def __set__(self, instance, value):
        pass


class Boolean(Argument):

    """ Represents a boolean. "1", "yes", "on" and "true" are all considered
    to be True boolean values. Anything else is False. """

    def __set__(self, instance, value):
        if isinstance(value, six.text_type):
            if value.lower() in ("1", "yes", "on", "true"):
                value = True
            else:
                value = False
        else:
            value = bool(value)
        setattr(instance, self.arg_id, value)


class String(Argument):

    """ Represents a string. """

    def __set__(self, instance, value):
        if value is not None:
            value = force_str(value)
        setattr(instance, self.arg_id, value)


class Integer(Argument):

    """ Represents an integer argument taken from the source file. This can
    throw an :py:exc:errors.ParseError if the passed in value cannot represent
    a base-10 integer. """

    def __set__(self, instance, value):
        if not isinstance(value, int):
            try:
                value = int(value)
            except ValueError:
                raise errors.InvalidParameter("%s is not an integer" % value)
        setattr(instance, self.arg_id, value)


class Octal(Integer):

    def __set__(self, instance, value):
        if not isinstance(value, int):
            value = int(value, 8)
        setattr(instance, self.arg_id, value)


class IPAddress(String):

    def __set__(self, instance, value):
        try:
            value = netaddr.IPAddress(value)
        except netaddr.core.AddrFormatError:
            raise errors.InvalidParameter("{} is not a valid IP Address")
        setattr(instance, self.arg_id, value)


class IPNetwork(String):

    def __set__(self, instance, value):
        try:
            value = netaddr.IPNetwork(value)
        except netaddr.core.AddrFormatError:
            raise errors.InvalidParameter("{} is not a valid IP Address")
        if value != value.cidr:
            raise errors.InvalidParameter("{} looks wrong - did you mean {}?".format(value, value.cdr))
        setattr(instance, self.arg_id, value)


class Dict(Argument):
    def __set__(self, instance, value):
        setattr(instance, self.arg_id, value)

    def default(self, instance):
        return {}


class List(Argument):
    def __set__(self, instance, value):
        setattr(instance, self.arg_id, value)


class TargetArgument(Argument):

    def __set__(self, instance, value):
        try:
            setattr(instance, self.arg_id, instance.targets[value])
        except KeyError:
            raise errors.InvalidTarget("'%s' not a valid target" % (value, ))

    def default(self, instance):
        if not instance.default_target:
            return target.NullTarget
        return instance.default_target


class Resource(Argument):

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

    def __set__(self, instance, value):
        """
        Every time you assign a value to a Resource argument we validate it is
        the correct type. We also mark self as depending on the resource.
        """
        if not isinstance(value, self.resource_class):
            raise errors.InvalidParameter("Parameter must be a {}".format(self.resource_class))
        instance.add_dependency(value)
        setattr(instance, self.arg_id, value)

    def contribute_to_class(self, cls):
        """
        If we mark a resource as being assignable to another resource then it
        automatically gains a factory method. Continuing the VPC+Subnet example,
        we can now::

            some_vpc.add_subnet(cidr_block='192.168.0.1/24')

        With this form you don't have to pass the vpc argument (it is done
        implicitly).
        """
        argument_name = self.argument_name

        def _(self, **kwargs):
            arguments = {argument_name: self}
            arguments.update(kwargs)
            resource = cls(self, **arguments)
            self.workspace.add_dependency(resource)
            return resource
        setattr(self.resource_class, 'add_%s' % cls.resource_name,  _)


class ResourceList(Argument):

    """
    An argument that represents a list of resources that we depend on.

    WARNING: A limitation at present is that you can only *set* a list. Do not
    mutate a resource list in place as it does not update the dependencies.
    """

    def __init__(self, resource_class, **kwargs):
        super(ResourceList, self).__init__(**kwargs)
        self.resource_class = resource_class

    def __set__(self, instance, value):
        for val in value:
            if not isinstance(val, self.resource_class):
                raise errors.InvalidParameter("Parameter must be a {}".format(self.resource_class))
            instance.add_dependency(val)
        setattr(instance, self.arg_id, value)
