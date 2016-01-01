# Copyright 2016 Isotoma Limited
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
from . import variable


class Integer(variable.Variable):

    resource_name = "integer"

    name = argument.String()
    default = argument.String()
    min = argument.String()
    max = argument.String()


class Set(variable.Plan):
    resource = Integer

    def to_string(self, value):
        return str(value)


class Get(variable.Plan):
    resource = Integer

    def from_string(self, value):
        return int(value)


argument.Integer.register_adapter(Integer, lambda r: r.value)
