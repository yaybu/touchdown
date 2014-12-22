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

from . import errors, policy
from .utils import force_str


class Argument(object):

    """ Stores the argument value on the instance object. It's a bit fugly,
    neater ways of doing this that do not involve passing extra arguments to
    Argument are welcome. """

    argument_id = 0
    default = None

    def __init__(self, **kwargs):
        self.default = kwargs.pop("default", self.default)
        self.__doc__ = kwargs.pop("help", None)
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
                raise errors.ParseError("%s is not an integer" % value)
        setattr(instance, self.arg_id, value)


class Octal(Integer):

    def __set__(self, instance, value):
        if not isinstance(value, int):
            value = int(value, 8)
        setattr(instance, self.arg_id, value)


class Dict(Argument):
    def __set__(self, instance, value):
        setattr(instance, self.arg_id, value)


class List(Argument):
    def __set__(self, instance, value):
        setattr(instance, self.arg_id, value)


class File(Argument):

    """ Provided with a URL, this can get files by various means. Often used
    with the package:// scheme """

    def __set__(self, instance, value):
        setattr(instance, self.arg_id, value)


class PolicyArgument(Argument):

    """ Parses the policy: argument for resources, including triggers etc. """

    def __set__(self, instance, value):
        try:
            setattr(instance, self.arg_id, instance.policies[value](instance))
        except KeyError:
            raise errors.InvalidPolicy("'%s' not a valid policy" % (value, ))

    def default(self, instance):
        if not instance.default_policy:
            return policy.NullPolicy(instance)
        return instance.default_policy(instance)
