
import click
from . import kvstore

@click.group()
def cli():
    pass

@cli.command()
@click.argument("key", type=str)
def get(key):
    if key in kvstore:
        click.echo(kvstore[key])

@cli.command()
@click.argument("key", type=str)
@click.argument("value", type=str)
def set(key, value):
    kvstore[key] = value

