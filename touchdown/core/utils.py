# Copyright 2014 Isotoma Limited
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


def force_str(s):
    if isinstance(s, str):
        return s
    elif isinstance(s, six.text_type):
        return s.encode('utf-8')
    elif isinstance(s, six.binary_type):
        return s.decode('utf-8')
    raise ValueError('{} Not a string'.format(s))


def force_unicode(s):
    if isinstance(s, six.binary_type):
        return s.decode('utf-8')
    elif isinstance(s, six.text_type):
        return s
    raise ValueError('Not a string')


def force_bytes(s):
    if isinstance(s, six.binary_type):
        return s
    elif isinstance(s, six.text_type):
        return s.encode('utf-8')
    raise ValueError('Not a string')


class cached_property(object):

    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, instance, owner):
        if instance is None:
            return self
        retval = instance.__dict__[self.func.__name__] = self.func(instance)
        return retval
