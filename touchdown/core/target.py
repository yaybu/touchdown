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
from . import errors


class TargetType(type):

    """ Registers the target on the resource """

    def __new__(meta, class_name, bases, new_attrs):
        cls = type.__new__(meta, class_name, bases, new_attrs)
        if getattr(cls, "resource", None) is not None:
            cls.resource.policies[cls.name] = cls
            if cls.default:
                cls.resource.default_target = cls
        return cls


class Target(six.with_metaclass(TargetType)):

    """
    A goal state for infrastructure based on a resource. For example, a target
    to move a resource towards existing or not existing.
    """

    # specify true if you wish this target to be the default
    default = False

    # the name of the target

    name = None

    # specify the resource to which this target applies
    resource = None

    # Override this with a list of assertions
    signature = ()

    def __init__(self, resource):
        super(Target, self).__init__()
        self.resource = resource

    def validate(self):
        a = AND(*self.signature)
        if a.test(self.resource):
            return

        msg = ["Resource doesn't confirm to the target %s" % self.name]
        msg.extend(a.describe(self.resource))
        raise errors.NonConformingPolicy("\n".join(msg))

    def get_actions(self, runner):
        return []


class NullTarget(Target):
    """ A target that doesn't do anything """


class ArgumentAssertion(object):

    """ An assertion of the state of an argument """

    def __init__(self, name):
        self.name = name


class Present(ArgumentAssertion):

    """ The argument has been specified, or has a default value. """

    def test(self, resource):
        """ Test that the argument this asserts for is present in the
        resource. """
        return resource.__args__[self.name].present(resource)

    def describe(self, resource):
        yield "'%s' must be present (%s)" % (self.name, self.test(resource))


class Absent(Present):

    """ The argument has not been specified by the user and has no default
    value. An argument with a default value is always defined. """

    def test(self, resource):
        return not super(Absent, self).test(resource)

    def describe(self, resource):
        yield "'%s' must be absent (%s)" % (self.name, self.test(resource))


class AND(ArgumentAssertion):

    def __init__(self, *args):
        self.args = args

    def test(self, resource):
        for a in self.args:
            if not a.test(resource):
                return False
        return True

    def describe(self, resource):
        yield "The follow conditions must all be met:"
        for a in self.args:
            for msg in a.describe(resource):
                yield "  " + msg
        yield ""


class NAND(ArgumentAssertion):

    def __init__(self, *args):
        self.args = args

    def test(self, resource):
        results = [1 for a in self.args if a.test(resource)]
        if len(results) > 1:
            return False
        return True

    def describe(self, resource):
        yield "No more than 1 of the following conditions should be true:"
        for a in self.args:
            for msg in a.describe(resource):
                yield "  " + msg
        yield ""


class XOR(ArgumentAssertion):

    def __init__(self, *args):
        self.args = args

    def test(self, resource):
        l = [1 for a in self.args if a.test(resource)]
        if len(l) == 0:
            return False
        elif len(l) == 1:
            return True
        else:
            return False

    def describe(self, resource):
        yield "Only one of the following conditions should be true:"
        for a in self.args:
            for msg in a.describe(resource):
                yield "  " + msg
        yield ""


class OR(ArgumentAssertion):

    def __init__(self, *args):
        self.args = args

    def test(self, resource):
        l = [1 for a in self.args if a.test(resource)]
        if len(l) == 0:
            return False
        else:
            return True

    def describe(self, resource):
        yield "At least one of the following conditions should be true:"
        for a in self.args:
            for msg in a.describe(resource):
                yield "  " + msg
        yield ""
