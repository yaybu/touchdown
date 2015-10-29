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

import threading

from touchdown.core.utils import force_str


class BaseFrontend(object):

    def failure(self, text):
        self.echo(text)

    def echo(self, text, nl=True, **kwargs):
        text = force_str(text)
        if threading.current_thread().name != "MainThread":
            text = "[{}] {}".format(threading.current_thread().name, text)
        if nl:
            self._echo("{}\n".format(text))
        else:
            self._echo(text)

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

    def render_plan(self, plan):
        for resource, actions in plan:
            self.echo("%s:" % resource)
            for action in actions:
                description = list(action.description)
                self.echo("  * %s" % description[0])
                for line in description[1:]:
                    self.echo("      %s" % line)
            self.echo("")

    def confirm_plan(self, plan):
        self.echo("Generated a plan to update infrastructure configuration:")
        self.echo("")
        self.render_plan(plan)
        return self.confirm("Do you want to continue?")

    def progressbar(self, **kwargs):
        raise NotImplementedError(self.progressbar)

    def prompt(self, message, key=None, default=None):
        raise NotImplementedError(self.prompt)

    def confirm(self, message):
        raise NotImplementedError(self.confirm)

    def start(self, subcommand, goal):
        pass

    def finish(self):
        pass
