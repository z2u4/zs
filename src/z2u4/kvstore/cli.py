
import json
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
@click.argument("value", type=str, required=False)
def set(key, value):
    if value is None:
        from tkinter import Tk
        value = Tk().clipboard_get()
    kvstore[key] = value

@cli.command()
def reset():
    kvstore.clear()
    click.echo("KVStore reset")

@cli.command()
@click.argument("file", type=click.Path())
def export(file):
    with open(file, "w") as f:
        json.dump(kvstore, f)
    click.echo("KVStore exported")


@cli.command()
def keys():
    click.echo(kvstore.keys())
