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


class Refresh(Goal):

    ''' Replace a configuration variable with its default setting '''

    name = 'refresh'
    mutator = False

    def get_plan_class(self, resource):
        plan_class = resource.meta.get_plan('refresh')
        if not plan_class:
            plan_class = resource.meta.get_plan('describe')
        if not plan_class:
            plan_class = resource.meta.get_plan('null')
        return plan_class

    @classmethod
    def setup_argparse(cls, parser):
        parser.add_argument(
            'name',
            metavar='NAME',
            type=str,
            help='The setting to refresh',
        )

    def execute(self, name):
        settings = self.collect_as_dict('refresh')
        if name not in settings:
            raise errors.Error('No such setting "{}"'.format(name))
        settings[name].execute()


register(Refresh)
