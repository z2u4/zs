import os
import shutil
import click
from z2u4.cacher.core import TYPES, CacheItemParams, Cacher


def processCliParams(args: list[str]) -> dict:
    params = {}
    for arg in args:
        if "=" not in arg and "url" not in params:
            assert "." in arg, "missing url features"
            assert "/" in arg, "missing url features"
            params["url"] = arg
        else:
            key, value = arg.split("=")
            assert key in CacheItemParams.__annotations__, f"invalid key: {key}"
            params[key] = value
    return params


@click.group()
def cli():
    pass


@cli.command("list")
@click.option("-c", "--cacheType", type=click.Choice(TYPES))
def _list(cachetype):
    from tabulate import tabulate

    if cachetype:
        items = Cacher.iter_type(cachetype)
    else:
        items = Cacher.iter_cache()
    processed = []
    for id, item in items:
        signature = item["meta"].get("url", None)

        processed.append([id, item["type"], signature])

    click.echo(tabulate(processed, headers=["ID", "Type", "Signature"]))


@cli.command("remove")
@click.option("--id", type=str)
@click.option("-c", "--cacheType", type=click.Choice(TYPES))
@click.option("-a", "--args", type=str, multiple=True)
def _remove(id, cachetype, args):
    if args:
        params = processCliParams(args)
        id = Cacher.cache(cachetype, **params, _check=False)
    Cacher.remove(id)


@cli.command()
@click.option("-f", "--force", is_flag=True)
def purge(force):
    if force:
        Cacher.purge()
        click.echo("Cache purged", color="red")
    else:
        directories = os.listdir(Cacher.CACHE_DIR)
        for id, _ in Cacher.iter_cache():
            if id in directories:
                directories.remove(id)

        if directories:
            click.echo(f"The following directories will be purged: {directories}")
            if click.confirm("Are you sure you want to proceed?"):
                for id in directories:
                    shutil.rmtree(
                        os.path.join(Cacher.CACHE_DIR, id), ignore_errors=True
                    )
                click.echo("Cache purged", color="red")
            else:
                click.echo("Cache not purged", color="red")


@cli.command()
@click.argument("cacheType", type=click.Choice(TYPES))
@click.argument("args", nargs=-1)
def testParams(cachetype, args):
    click.echo(f"Recieved Cache Type:\t {cachetype}")
    click.echo(f"Recieved Args:\t {args}")
    params = processCliParams(args)
    results = Cacher.process_params(cachetype, params)
    click.echo(f"Results:\t {results}")


@cli.command()
@click.argument("cacheType", type=click.Choice(TYPES))
@click.argument("args", nargs=-1)
def cache(cachetype, args):
    params = processCliParams(args)
    res = Cacher.cache(cachetype, **params)
    if res:
        click.echo(f"Item cached at {res}")


@cli.command()
@click.option("--id", type=str)
@click.option("-c", "--cacheType", type=click.Choice(TYPES))
@click.option("-a", "--args", type=str, multiple=True)
@click.option("-f", "--force", is_flag=True)
def check(id, cachetype, args, force):
    if args:
        params = processCliParams(args)
        id = Cacher.cache(cachetype, **params)
    res = Cacher.check(id, force)
    if not res:
        click.echo(f"Item {id} is not due for checking")


@cli.command()
@click.argument("path", type=str)
@click.option("--id", type=str)
@click.option("-c", "--cacheType", type=click.Choice(TYPES))
@click.option("-a", "--args", type=str, multiple=True)
def fpath(path, id, cachetype, args):
    if id or args:
        if args:
            assert cachetype, "cache type is required"
            params = processCliParams(args)
            id = Cacher.cache(cachetype, **params)
        else:
            assert id, "id is required"
    else:
        pass


@cli.command()
@click.argument("string", type=str)
def query(string):
    res = Cacher.query(string)
    click.echo(res)


@cli.command()
@click.argument("id", required=False)
def open(id):
    if not id:
        return os.startfile(Cacher.CACHE_DIR)
    os.startfile(os.path.join(Cacher.CACHE_DIR, id))


if __name__ == "__main__":
    cli()
