from functools import cache

import os
from zuu.PKG.importlib import import_file
from zuu.STRUCT.dict_with_autosave import DictWithAutosave

PATH = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
BASEPATH = os.path.dirname(PATH)

USRPATH = os.path.join(os.path.expanduser("~"), ".z2u4", "zs")
os.makedirs(USRPATH, exist_ok=True)
_USRPATH_CONFIG_PATH = os.path.join(USRPATH, "config.json")

# this config -> key (name) : value {uuid, url}
USRPATH_CONFIG = DictWithAutosave(_USRPATH_CONFIG_PATH)
USRPATH_CONFIG.setdefault("aliases", {})
USRPATH_CONFIG.setdefault("shells", {})

@cache
def gather_installed_mods() -> list[dict]:
    mods = []
    for fo in os.listdir(BASEPATH):
        path = os.path.join(BASEPATH, fo)
        if not os.path.isdir(path):
            continue

        if fo.startswith("__"):
            continue

        mods.append(
            {
                "name": fo,
                "path": path,
                "last_modified": os.path.getmtime(path),
                "created": os.path.getctime(path),
            }
        )

    return mods

@cache
def gather_installed_shells():
    shells = {}
    for mod in gather_installed_mods():
        path = mod["path"]
        cli_path = os.path.join(path, "cli.py")

        if not os.path.exists(cli_path):
            continue

        filemod = import_file(cli_path, f"z2u4.{mod['name']}")

        shells[mod["name"]] = filemod

    return shells

def get_shell_path(path : str):
    if os.path.exists(os.path.join(path, "cli.py")):
        return os.path.join(path, "cli.py"), None
    elif os.path.exists(os.path.join(path, "src", "cli.py")):
        return os.path.join(path, "src", "cli.py"), None
    elif (
        os.path.exists(os.path.join(path, "src"))
        and len(
            kk := [
                x
                for x in os.listdir(os.path.join(path, "src"))
                if os.path.isdir(os.path.join(path, "src", x))
                and not x.startswith("__")
            ]
        )
        == 1
    ):
        return os.path.join(path, "src", kk[0], "cli.py"), kk[0]

@cache
def gather_installed_shells_from_usrpath():
    from z2u4.cacher.core import Cacher

    shells = {}

    for name, id in USRPATH_CONFIG.get("shells", {}).items():
        path = Cacher.get_path(id)
        res = get_shell_path(path)  
        if res:
            cli_path, mod_name = res
            filemod = import_file(cli_path, mod_name)
            shells[name] = filemod
        else:
            continue

    return shells
