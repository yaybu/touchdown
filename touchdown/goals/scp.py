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


class Scp(Goal):

    ''' SCP files to and from infrastructure managed by touchdown '''

    name = 'scp'
    mutator = False

    def get_plan_class(self, resource):
        plan_class = resource.meta.get_plan('scp')
        if not plan_class:
            plan_class = resource.meta.get_plan('describe')
        if not plan_class:
            plan_class = resource.meta.get_plan('null')
        return plan_class

    @classmethod
    def setup_argparse(cls, parser):
        parser.add_argument(
            'source',
            metavar='SOURCE',
            type=str,
            help='What to copy',
        )
        parser.add_argument(
            'destination',
            metavar='DESTINATION',
            type=str,
            help='Where to copy it',
        )

    def execute(self, source, destination):
        for path in (source, destination):
            if ':' in path:
                server = path.split(':', 1)[0]
                break
        else:
            raise errors.Error('Either source or destination must contain a target server that touchdown knows about')

        boxes = self.collect_as_dict('scp')
        if server not in boxes:
            raise errors.Error('No such host "{}"'.format(server))

        boxes[server].execute(source, destination)

register(Scp)
