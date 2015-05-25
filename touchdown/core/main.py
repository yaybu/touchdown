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

from touchdown.core.workspace import Workspace
from touchdown.core import errors, goals, map


class ConsoleInterface(object):

    def __init__(self, interactive=True):
        self.interactive = interactive

    def echo(self, text, nl=True, **kwargs):
        if nl:
            click.echo("{}\n".format(text), nl=False, **kwargs)
        else:
            click.echo("{}".format(text), nl=False, **kwargs)

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


def get_goal(ctx, target):
    return goals.create(
        target,
        ctx.parent.obj,
        ConsoleInterface(),
        map=map.ParallelMap if not ctx.parent.params['serial'] else map.SerialMap
    )


@click.group()
@click.option('--debug/--no-debug', default=False, envvar='DEBUG')
@click.option('--serial/--parallel', default=False, envvar='SERIAL')
@click.pass_context
def main(ctx, debug, serial):
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
    r = get_goal(ctx, "apply")
    try:
        r.apply()
    except errors.Error as e:
        raise click.ClickException(str(e))


@main.command()
@click.pass_context
def destroy(ctx):
    r = get_goal(ctx, "destroy")
    try:
        r.apply()
    except errors.Error as e:
        raise click.ClickException(str(e))


@main.command()
@click.pass_context
def plan(ctx):
    r = get_goal(ctx, "apply")
    r.ui.render_plan(r.plan())


@main.command()
@click.pass_context
def dot(ctx):
    get_goal(ctx, "dot").execute()


@main.command()
@click.pass_context
def tail(ctx):
    get_goal(ctx, "tail").execute()


if __name__ == "__main__":
    main()
