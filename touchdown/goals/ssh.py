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

from touchdown.core import errors
from touchdown.core.goals import Goal, register


class Ssh(Goal):

    """ SSH into infrastructure managed by touchdown """

    name = "ssh"
    mutator = False

    def get_plan_class(self, resource):
        plan_class = resource.meta.get_plan("ssh")
        if not plan_class:
            plan_class = resource.meta.get_plan("null")
        return plan_class

    def execute(self, box):
        boxes = self.collect_as_dict("ssh")
        if box not in boxes:
            raise errors.Error("No such host '{}'".format(box))
        boxes[box].execute()

register(Ssh)
