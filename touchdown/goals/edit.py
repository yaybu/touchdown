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


class Edit(Goal):

    ''' Edit a file like object managed by Touchdown '''

    name = 'edit'
    mutator = False

    def get_plan_class(self, resource):
        plan_class = resource.meta.get_plan('edit')
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
            help='The file to edit',
        )

    def execute(self, name):
        files = self.collect_as_dict('edit')
        if name not in files:
            raise errors.Error('No such file "{}"'.format(name))
        files[name].execute()

register(Edit)
