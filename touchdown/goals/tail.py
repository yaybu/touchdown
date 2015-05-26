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


class Tail(Goal):

    """ Inspect (and stream) your logs """

    name = "tail"

    def get_plan_class(self, resource):
        plan_class = resource.meta.get_plan("tail")
        if not plan_class:
            plan_class = resource.meta.get_plan("null")
        return plan_class

    @classmethod
    def setup_argparse(cls, parser):
        parser.add_argument("stream", metavar="STREAM", type=str, help="The logstream to tail")
        parser.add_argument("-f", "--follow", default=False, action="store_true", help="Don't exit and continue to print new events in the log stream")
        parser.add_argument("-s", "--start", default="5m ago", action="store", help="The earliest event to retrieve")
        parser.add_argument("-e", "--end", default=None, action="store", help="The latest event to retrieve")

    def execute(self, args):
        tailers = {}

        def _(e, r):
            p = self.get_plan(r)
            if p.name == "tail":
                tailers[p.resource.name] = p

        for progress in self.Map(self.get_plan_order(), _, self.ui.echo):
            self.ui.echo("\r[{: >6.2%}] Building plan...".format(progress), nl=False)
        self.ui.echo("")

        if args.stream not in tailers:
            raise errors.Error("No such log group '{}'".format(args.stream))

        tailers[args.stream].tail(args.start, args.end, args.tail)

register(Tail)
