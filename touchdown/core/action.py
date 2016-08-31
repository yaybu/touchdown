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


class Action(object):

    def __init__(self, plan):
        self.plan = plan
        self.runner = plan.runner
        self.resource = plan.resource

    def get_plan(self, resource):
        return self.runner.get_plan(resource)

    def __str__(self):
        return '\n'.join(self.description)
