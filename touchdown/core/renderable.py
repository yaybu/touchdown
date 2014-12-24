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

from . import errors
from .resource import Resource


class Renderable(object):

    def attach(self, node):
        """
        Anything that wants to depend on this renderable needs to depend on all
        these other things
        """
        raise NotImplementedError(self.attach)

    def render(self):
        """
        Render a value.
        """
        raise NotImplementedError(self.render)


 class Property(Renderable):

     """
     Lazy 'getattr'
     """

    def __init__(self, object, attribute):
        if not isinstance(object, Resource):
            raise errors.ValueError("'object' is not a resource")
        self.object = object
        self.attribute = attribute

    def attach(self, node):
        node.add_dependency(self.object)

    def render(self):
        return getattr(self.object, self.attribute)


class Format(Renderable):

    """
    Lazy 'just in time' evaluation of python "format strings".

    For example::

        aws.add_ami(
            description=Format(
                "tag={github.tag}, date={now}",
                github=some_object,
                now=some_other_object,
            )
        )

    The description property won't be evaluated until it's needed. And the AMI
    won't be build until all the pre-requisites are available.
    """

    def __init__(self, format_string, *args, **kwargs):
        self.format_string = format_string
        self.args = args
        self.kwargs = kwargs

    def attach(self, node):
        for obj in self.args:
            if isinstance(obj, Resource):
                node.add_dependency(obj)
        for obj in self.kwargs.values():
            if isinstance(obj, Resource):
                node.add_dependency(obj)

    def render(self):
        return self.format_string.format(*args, **kwargs)
