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
from touchdown.core.datetime import parse_datetime
from touchdown.core.goals import Goal, register


def datetime(value):
    try:
        return parse_datetime(value)
    except errors.Error:
        import argparse
        raise argparse.ArgumentTypeError(
            '{} is not a valid date/time'.format(value),
        )


class Tail(Goal):

    ''' Inspect (and stream) your logs '''

    name = 'tail'
    mutator = False

    def get_plan_class(self, resource):
        plan_class = resource.meta.get_plan('tail')
        if not plan_class:
            plan_class = resource.meta.get_plan('null')
        return plan_class

    @classmethod
    def setup_argparse(cls, parser):
        parser.add_argument(
            'stream',
            metavar='STREAM',
            type=str,
            help='The logstream to tail'
        )
        parser.add_argument(
            '-f',
            '--follow',
            default=False,
            action='store_true',
            help='Don\'t exit and continue to print new events in the stream'
        )
        parser.add_argument(
            '-s',
            '--start',
            default='5m ago',
            action='store',
            type=datetime,
            help='The earliest event to retrieve'
        )
        parser.add_argument(
            '-e',
            '--end',
            default=None,
            action='store',
            type=datetime,
            help='The latest event to retrieve'
        )

    def execute(self, stream, start='5m ago', end=None, follow=False):
        tailers = self.collect_as_dict('tail')
        if stream not in tailers:
            raise errors.Error('No such log stream "{}"'.format(stream))
        tailers[stream].tail(start, end, follow)

register(Tail)
