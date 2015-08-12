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

from __future__ import absolute_import, print_function

import six
import threading

from .progress import ProgressBar


class ConsoleFrontend(object):

    def __init__(self, interactive=True):
        self.interactive = interactive

    def failure(self, text):
        # FIXME: Colorize this?
        self.echo(text)

    def echo(self, text, nl=True, **kwargs):
        if threading.current_thread().name != "MainThread":
            text = "[{}] {}".format(threading.current_thread().name, text)
        if nl:
            print("{}\n".format(text), end='')
        else:
            print("{}".format(text), end='')

    def progressbar(self, **kwargs):
        return ProgressBar(**kwargs)

    def table(self, data):
        widths = {}
        for row in data:
            for i, column in enumerate(row):
                widths[i] = max(len(column), widths.get(i, 0))

        line = "| " + " | ".join(
            "{{:<{}}}".format(widths[i]) for i in range(len(widths))
        ) + " |"

        sep = "+-" + "-+-".join("-" * widths[i] for i in range(len(widths))) + "-+"

        self.echo(sep)
        self.echo(line.format(*data[0]))
        self.echo(sep)
        for row in data[1:]:
            self.echo(line.format(*row))
        self.echo(sep)

    def prompt(self, message, key=None):
        response = six.moves.input('{}: '.format(message))
        while not response:
            response = six.moves.input('{}: '.format(message))
        return response

    def confirm(self, message):
        response = six.moves.input('{} [Y/n] '.format(message))
        while response.lower() not in ('y', 'n', ''):
            response = six.moves.input('{} [Y/n] '.format(message))
        return response.lower() != 'n'

    def render_plan(self, plan):
        for resource, actions in plan:
            print("%s:" % resource)
            for action in actions:
                description = list(action.description)
                print("  * %s" % description[0])
                for line in description[1:]:
                    print("      %s" % line)
            print("")

    def confirm_plan(self, plan):
        print("Generated a plan to update infrastructure configuration:")
        print()

        self.render_plan(plan)

        if not self.interactive:
            return True

        return self.confirm("Do you want to continue?")
