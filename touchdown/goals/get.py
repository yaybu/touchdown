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


class Get(Goal):

    ''' Get a configuration variable '''

    name = 'get'
    mutator = False

    def get_plan_class(self, resource):
        plan_class = resource.meta.get_plan('get')
        if not plan_class:
            plan_class = resource.meta.get_plan('null')
        return plan_class

    @classmethod
    def setup_argparse(cls, parser):
        parser.add_argument(
            'name',
            metavar='NAME',
            type=str,
            help='The setting to set',
        )

    def execute(self, name):
        settings = self.collect_as_dict('get')
        if name not in settings:
            raise errors.Error('No such setting "{}"'.format(name))
        val, user_set = settings[name].execute()
        val = settings[name].to_string(val)

        if user_set:
            self.ui.echo('{} (overriden by user)'.format(val))
        else:
            self.ui.echo('{} (default value)'.format(val))

register(Get)
