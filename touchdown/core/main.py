# Copyright 2014-2015 Isotoma Limited
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

from __future__ import print_function

import argparse
import inspect
import logging
import sys
import six

from touchdown.core.workspace import Touchdownfile
from touchdown.core import errors, goals, map


class ConsoleInterface(object):

    def __init__(self, interactive=True):
        self.interactive = interactive

    def echo(self, text, nl=True, **kwargs):
        if nl:
            print("{}\n".format(text), end='')
        else:
            print("{}".format(text), end='')

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


class SubCommand(object):

    def __init__(self, goal, workspace, console):
        self.goal = goal
        self.workspace = workspace
        self.console = console

    def get_args_and_kwargs(self, callable, namespace):
        argspec = inspect.getargspec(callable)
        args = []
        for arg in argspec.args[1:]:
            args.append(getattr(namespace, arg))
        kwargs = {}
        for k, v in namespace._get_kwargs():
            if k not in argspec.args and argspec.keywords:
                kwargs[k] = v
        return args, kwargs

    def __call__(self, args):
        self.workspace.load()
        try:
            g = self.goal(
                self.workspace,
                self.console,
                map.ParallelMap if not args.serial else map.SerialMap
            )
            args, kwargs = self.get_args_and_kwargs(g.execute, args)
            return g.execute(*args, **kwargs)
        except errors.Error as e:
            self.console.echo(str(e))
            sys.exit(1)


def configure_parser(parser, workspace, console):
    parser.add_argument("--debug", default=False, action="store_true")
    parser.add_argument("--serial", default=False, action="store_true")
    parser.add_argument("--unattended", default=False, action="store_true")

    sub = parser.add_subparsers()
    for name, goal in goals.registered():
        p = sub.add_parser(name, help=getattr(goal, "__doc__", ""))
        goal.setup_argparse(p)
        p.set_defaults(func=SubCommand(
            goal,
            workspace,
            console,
        ))


def main():
    parser = argparse.ArgumentParser(description="Manage your infrastructure")
    console = ConsoleInterface()
    configure_parser(parser, Touchdownfile(), console)
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")

    console.interactive = not args.unattended

    args.func(args)


if __name__ == "__main__":
    main()
