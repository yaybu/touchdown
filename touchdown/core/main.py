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

import logging

import click

from touchdown.core.runner import Runner
from touchdown.core.workspace import Workspace
from touchdown.core import errors


class ConsoleInterface(object):

    def __init__(self, interactive=True):
        self.interactive = interactive

    def echo(self, text):
        click.echo(text)

    def progress(self, iterable, label=None, length=None):
        return click.progressbar(iterable, label=label, length=length)

    def render_plan(self, plan):
        for resource, actions in plan:
            click.echo("%s:" % resource)
            for action in actions:
                description = list(action.description)
                click.echo("  * %s" % description[0])
                for line in description[1:]:
                    click.echo("      %s" % line)
            click.echo("")

    def confirm_plan(self, plan):
        click.echo("Generated a plan to update infrastructure configuration:")
        click.echo()

        self.render_plan(plan)

        if not self.interactive:
            return True

        return click.confirm("Do you want to continue?")


@click.group()
@click.option('--debug/--no-debug', default=False, envvar='DEBUG')
@click.pass_context
def main(ctx, debug):
    if debug:
        logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")
    g = {"workspace": Workspace()}
    with open("Touchdownfile") as f:
        code = compile(f.read(), "Touchdownfile", "exec")
        exec(code, g)
    ctx.obj = g['workspace']


@main.command()
@click.pass_context
def apply(ctx):
    r = Runner("apply", ctx.obj, ConsoleInterface())
    try:
        r.apply()
    except errors.Error as e:
        raise click.ClickException(str(e))


@main.command()
@click.pass_context
def destroy(ctx):
    r = Runner("destroy", ctx.obj, ConsoleInterface())
    try:
        r.apply()
    except errors.Error as e:
        raise click.ClickException(str(e))


@main.command()
@click.pass_context
def plan(ctx):
    r = Runner("apply", ctx.obj, ConsoleInterface())
    r.ui.render_plan(r.plan())


@main.command()
@click.pass_context
def dot(ctx):
    r = Runner("apply", ctx.obj, ConsoleInterface())
    click.echo(r.dot())


if __name__ == "__main__":
    main()
