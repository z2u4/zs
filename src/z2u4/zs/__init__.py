import datetime
import click
from tabulate import tabulate

from z2u4.zs.selfResolve import USRPATH_CONFIG


fts = lambda x: datetime.datetime.fromtimestamp(x).strftime("%Y-%m-%d %H:%M:%S")  # noqa


@click.group()
def cli():
    pass


@cli.command("list")
def _list():
    from z2u4.zs.selfResolve import gather_installed_mods

    mods = gather_installed_mods()

    mods = [[mod["name"], fts(mod["last_modified"]), ["PyInstalled"]] for mod in mods]
    click.echo(
        tabulate(mods, headers=["Name", "Last Modified", "Tags"], tablefmt="grid")
    )


@cli.command()
@click.argument("url")
def add(url):
    assert url.endswith(".git"), "URL must end with .git"
    from z2u4.cacher.core import Cacher
    from z2u4.zs.selfResolve import get_shell_path

    id = Cacher.cache(type_="gitRepo", url=url)
    item = Cacher.CACHE[id]
    path = Cacher.get_path(id)
    shelltest = get_shell_path(path)
    if not shelltest:
        click.echo(f"No shell found for {url}")
        return

    USRPATH_CONFIG["shells"][item["meta"]["repo"]] = id
    USRPATH_CONFIG._save()
    click.echo(f"Added {url} to cache")

@cli.command()
@click.argument("name")
@click.option("--clear-cache", "-c", is_flag=True, help="Clear the cacher too")
def remove(name, clear_cache):
    from z2u4.zs.selfResolve import USRPATH_CONFIG
    if name in USRPATH_CONFIG["aliases"].values():
        for n, a in USRPATH_CONFIG["aliases"].items():
            if a == name:
                name = n
                del USRPATH_CONFIG["aliases"][n]
                break

    id = USRPATH_CONFIG["shells"][name]
    del USRPATH_CONFIG["shells"][name]
    USRPATH_CONFIG._save()
    
    click.echo(f"Removed {name} from cache")

    if clear_cache:
        from z2u4.cacher.core import Cacher
        Cacher.remove(id)    
        click.echo(f"Removed {name} from cache")

@cli.command()
def list():
    from z2u4.zs.selfResolve import gather_installed_shells_from_usrpath, gather_installed_shells

    shells = gather_installed_shells_from_usrpath()
    click.echo("Installed from USRPATH:")
    for name, shell in shells.items():
        click.echo(name)    

    click.echo("\nInstalled from Z2U4:")
    shells = gather_installed_shells()
    for name, shell in shells.items():
        click.echo(name)

@cli.group()
def alias():
    pass

@alias.command("set")
@click.argument("name")
@click.argument("alias")
def alias_set(name, alias):
    from z2u4.zs.selfResolve import USRPATH_CONFIG
    USRPATH_CONFIG["aliases"][name] = alias
    USRPATH_CONFIG._save()
    click.echo(f"Set name {name} to alias {alias}")

@alias.command("remove")
@click.argument("alias")
def alias_remove(alias):
    from z2u4.zs.selfResolve import USRPATH_CONFIG
    for n, a in USRPATH_CONFIG["aliases"].items():
        if a == alias:
            del USRPATH_CONFIG["aliases"][n]
            USRPATH_CONFIG._save()
            click.echo(f"Removed alias {alias}")
            break

@alias.command("list")
def alias_list():
    from z2u4.zs.selfResolve import USRPATH_CONFIG
    click.echo(USRPATH_CONFIG["aliases"])

@cli.group()
def run():
    pass


def _run():
    from z2u4.zs.selfResolve import gather_installed_shells, gather_installed_shells_from_usrpath

    shells = gather_installed_shells()
    for name, shell in shells.items():
        run.add_command(shell.cli, name)

    shells = gather_installed_shells_from_usrpath()
    for name, shell in shells.items():
        run.add_command(shell.cli, name)
        alias = USRPATH_CONFIG["aliases"].get(name, None)
        if alias and alias not in run.commands:
            run.add_command(shell.cli, alias)

    cli()


if __name__ == "__main__":
    _run()
