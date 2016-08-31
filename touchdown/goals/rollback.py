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


class Rollback(Goal):

    ''' Rollback a database to a point in time or a backup '''

    name = 'rollback'
    mutator = False

    def get_plan_class(self, resource):
        plan_class = resource.meta.get_plan('rollback')
        if not plan_class:
            plan_class = resource.meta.get_plan('null')
        return plan_class

    @classmethod
    def setup_argparse(cls, parser):
        parser.add_argument(
            'target',
            metavar='TARGET',
            type=str,
            help='The resource to rollback',
        )
        parser.add_argument(
            'from_backup',
            metavar='FROM',
            type=str,
            help='When or what to rollback to',
        )

    def pre_restore(self):
        pass

    def post_restore(self):
        pass

    def execute(self, target, from_backup):
        restorable = self.collect_as_dict('rollback')
        if target not in restorable:
            raise errors.Error('No such resource "{}"'.format(target))
        restorable[target].check(from_backup)
        self.pre_restore()
        restorable[target].rollback(from_backup)
        self.post_restore()

register(Rollback)
