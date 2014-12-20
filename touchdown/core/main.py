import click


@click.group
@click.option('--debug/--no-debug', default=False, envvar='DEBUG')
@click.pass_context
def main(ctx, debug):
    click.echo("Hello")
