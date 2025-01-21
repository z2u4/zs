import datetime
import logging
import os
import pprint
import shutil
from typing import TypedDict
import typing
import uuid
from zuu.STRUCT.dict_with_autosave import DictWithAutosave
from .utils import (
    convert_url_to_raw,
    extract_githubrelease_params,
    extract_githuburl_params,
    extract_raw_params,
)

USRPATH = os.path.join(os.path.expanduser("~"), ".z2u4", "cacher")
os.makedirs(USRPATH, exist_ok=True)

TYPES = [
    "githubGist",
    "githubRawFile",
    "githubRelease",
    "webTarget",
    "localTarget",
    "gitRepo",
]
TYPE_LITERAL = typing.Literal[
    "githubGist",
    "githubRawFile",
    "githubRelease",
    "webTarget",
    "localTarget",
    "gitRepo",
]


class CacheItemParams(TypedDict, total=False):
    # repo
    url: str

    # broken down
    owner: str
    repo: str

    # repo
    branch: str

    # github file | local target
    path: str

    # gist
    id: str

    # release
    releaseTag: str
    asset: str
    assets: typing.List[str]


class CacheItem(TypedDict):
    type: TYPE_LITERAL
    lastChecked: float
    checkInterval: typing.Optional[int]
    meta: CacheItemParams


class Cacher:
    CACHE_PATH = os.path.join(USRPATH, "cache.json")
    try:
        CACHE: typing.Dict[str, CacheItem] = DictWithAutosave(CACHE_PATH)
    except:  # noqa
        CACHE = None
    CACHE_DIR = os.path.join(USRPATH, "cache")

    @classmethod
    def query(cls, string: str):
        if string in cls.CACHE:
            return cls.CACHE[string]

        for CTYPE in TYPES:
            if string.startswith(CTYPE + "/"):
                for id, item in cls.iter_type(CTYPE):
                    nonTyped = string[len(CTYPE) + 1 :]
                    if nonTyped == id:
                        return item

                    if nonTyped in item["meta"].values():
                        return item

        for id, item in cls.iter_cache():
            if string in item["meta"].values():
                return item

    @classmethod
    def purge(cls):
        os.remove(cls.CACHE_PATH)
        cls.CACHE = DictWithAutosave(cls.CACHE_PATH)
        shutil.rmtree(cls.CACHE_DIR, ignore_errors=True)
        os.makedirs(cls.CACHE_DIR, exist_ok=True)

    @classmethod
    def iter_cache(cls) -> typing.Iterator[tuple[str, CacheItem]]:
        for key, value in cls.CACHE.items():
            yield key, value

    @classmethod
    def iter_type(cls, type: TYPE_LITERAL) -> typing.Iterator[tuple[str, CacheItem]]:
        for key, value in cls.iter_cache():
            if value["type"] == type:
                yield key, value

    @classmethod
    def remove(cls, id: str):
        if id not in cls.CACHE:
            raise ValueError(f"Item {id} not found")
        del cls.CACHE[id]
        cls.CACHE._save()
        shutil.rmtree(os.path.join(cls.CACHE_DIR, id), ignore_errors=True)

    @classmethod
    def process_params(
        cls, type_: TYPE_LITERAL, kwargs: typing.Unpack[CacheItemParams]
    ) -> dict:
        if type_ == "githubGist":
            if "url" in kwargs:
                assert kwargs["url"].startswith(
                    "https://gist.github.com/"
                ), "URL must start with https://gist.github.com/"
                kwargs["owner"], kwargs["id"] = kwargs["url"].split("/")[-2:]
            else:
                assert (
                    "owner" in kwargs and "id" in kwargs
                ), "Either url or owner and id must be provided"
                kwargs["url"] = (
                    f"https://gist.github.com/{kwargs['owner']}/{kwargs['id']}"
                )

        elif type_ == "githubRawFile":
            if "url" in kwargs and not kwargs["url"].startswith(
                "https://raw.githubusercontent.com/"
            ):
                kwargs["url"], raw_params = convert_url_to_raw(kwargs["url"])
                kwargs["owner"] = raw_params["owner"]
                kwargs["repo"] = raw_params["repo"]
                kwargs["branch"] = raw_params["branch"]
                kwargs["path"] = raw_params["path"]

            elif "url" in kwargs:
                raw = extract_raw_params(kwargs["url"])
                kwargs["owner"] = raw["owner"]
                kwargs["repo"] = raw["repo"]
                kwargs["branch"] = raw["branch"]
                kwargs["path"] = raw["path"]
            else:
                assert "owner" in kwargs, "owner must be provided"
                assert "repo" in kwargs, "repo must be provided"
                assert "branch" in kwargs, "branch must be provided"
                assert "path" in kwargs, "path must be provided"
                kwargs["url"] = (
                    f"https://raw.githubusercontent.com/{kwargs['owner']}/{kwargs['repo']}/{kwargs['branch']}/{kwargs['path']}"
                )
        elif type_ == "gitRepo":
            if "url" in kwargs and kwargs["url"].startswith("https://github.com/"):
                if kwargs["url"].endswith(".git"):
                    kwargs["url"] = kwargs["url"][:-3]
                raw_params = extract_githuburl_params(kwargs["url"])
                kwargs["owner"] = raw_params["owner"]
                kwargs["repo"] = raw_params["repo"]
                kwargs["branch"] = raw_params["branch"]

                kwargs["url"] = (
                    f"https://github.com/{kwargs['owner']}/{kwargs['repo']}.git"
                )

            elif "url" in kwargs and kwargs["url"].startswith(
                "https://raw.githubusercontent.com/"
            ):
                raw_params = extract_raw_params(kwargs["url"])
                kwargs["owner"] = raw_params["owner"]
                kwargs["repo"] = raw_params["repo"]
                kwargs["branch"] = raw_params["branch"]

                kwargs["url"] = (
                    f"https://github.com/{kwargs['owner']}/{kwargs['repo']}.git"
                )

            else:
                assert "owner" in kwargs, "owner must be provided"
                assert "repo" in kwargs, "repo must be provided"

                kwargs["url"] = (
                    f"https://github.com/{kwargs['owner']}/{kwargs['repo']}.git"
                )

        elif type_ == "githubRelease":
            if "url" in kwargs:
                raw = extract_githubrelease_params(kwargs["url"])
                kwargs["owner"] = raw["owner"]
                kwargs["repo"] = raw["repo"]
                kwargs["releaseTag"] = raw["releaseTag"]
            else:
                assert "owner" in kwargs, "owner must be provided"
                assert "repo" in kwargs, "repo must be provided"
                kwargs["url"] = f"https://github.com/{kwargs['owner']}/{kwargs['repo']}"
                kwargs["url"] = (
                    f"{kwargs['url']}/releases/tag/{kwargs['releaseTag']}"
                    if "releaseTag" in kwargs
                    else f"{kwargs['url']}/releases/latest"
                )

        elif type_ == "webTarget":
            assert "url" in kwargs, "url must be provided"

        elif type_ == "localTarget":
            assert "path" in kwargs, "path must be provided"
            assert os.path.exists(kwargs["path"]), "path must exist"

        else:
            raise ValueError(f"Invalid type: {type_}")

        return kwargs

    @classmethod
    def shouldCheck(cls, id: str):
        item = cls.CACHE[id]
        lastChecked = datetime.datetime.fromtimestamp(item["lastChecked"])
        logging.info(f"Item {id} last checked: {lastChecked}")
        if "checkInterval" not in item:
            return False
        if (
            lastChecked + datetime.timedelta(seconds=item["checkInterval"])
            < datetime.datetime.now()
        ):
            return True
        return False

    @classmethod
    def check(cls, id: str, force: bool = False):
        # not force
        # not due for checking
        # not empty
        if not force and not cls.shouldCheck(id) and not len(os.listdir(cls.get_path(id))) == 0:
            logging.info(f"Item {id} is not due for checking")
            return 0

        cls.renew(id)
        return 1

    @classmethod
    def cache(
        cls,
        type_: TYPE_LITERAL,
        _check: bool = True,
        _checkInteval: typing.Optional[int] = 24 * 60 * 60,
        **kwargs: typing.Unpack[CacheItemParams],
    ) -> str:
        params = cls.process_params(type_, kwargs)
        for id, item in cls.iter_type(type_):
            if item["meta"] == params:
                if _check:
                    cls.check(id)
                return id

        id = str(uuid.uuid4())
        print("Caching item", id)
        cls.CACHE[id] = {
            "type": type_,
            "lastChecked": datetime.datetime.now().timestamp(),
            "checkInterval": _checkInteval,
            "meta": params,
        }
        cls.renew(id)
        return id

    @classmethod
    def renew(cls, id: str):
        item = cls.CACHE[id]

        specfunc = getattr(cls, f"renew_{item['type']}")
        specfunc(id, item)
        item["lastChecked"] = datetime.datetime.now().timestamp()
        cls.CACHE._save()

    @classmethod
    def renew_githubRawFile(cls, id: str, item: CacheItem):
        from zuu.APP.github import download_raw_content

        os.makedirs(os.path.join(cls.CACHE_DIR, id), exist_ok=True)
        download_raw_content(item["meta"]["url"], os.path.join(cls.CACHE_DIR, id))

    @classmethod
    def renew_githubRelease(cls, id: str, item: CacheItem):
        from zuu.APP.github import download_release, release_meta, get_releases

        os.makedirs(os.path.join(cls.CACHE_DIR, id), exist_ok=True)
        asset = item["meta"].get("asset", None)
        assets = item["meta"].get("assets", [])
        if asset:
            assets.append(asset)
        if not assets:
            assets = None
        rtag = item["meta"].get("releaseTag", "latest")
        if rtag == "latest":
            meta = get_releases(
                repo=f"{item['meta']['owner']}/{item['meta']['repo']}",
                limit=1,
            )
            meta = meta[0]
        else:
            meta = release_meta(
                repo=item["meta"]["repo"],
                name=rtag,
            )
        pprint.pprint(meta)
        download_release(
            meta,
            save_path=os.path.join(cls.CACHE_DIR, id),
            match_type="glob",
            asset_names=[".*"],
        )

    @classmethod
    def renew_githubGist(cls, id: str, item: CacheItem):
        from zuu.APP.github import download_gist

        os.makedirs(os.path.join(cls.CACHE_DIR, id), exist_ok=True)
        download_gist(
            gist_id=f"{item['meta']['owner']}/{item['meta']['id']}",
            save_path=os.path.join(cls.CACHE_DIR, id),
        )

    @classmethod
    def renew_webTarget(cls, id: str, item: CacheItem):
        import requests

        os.makedirs(os.path.join(cls.CACHE_DIR, id), exist_ok=True)
        for file in requests.get(item["meta"]["url"]).iter_content(chunk_size=1024):
            with open(os.path.join(cls.CACHE_DIR, id, file.name), "wb") as f:
                f.write(file)

    @classmethod
    def renew_localTarget(cls, id: str, item: CacheItem):
        import shutil

        os.makedirs(os.path.join(cls.CACHE_DIR, id), exist_ok=True)
        shutil.copy(item["meta"]["path"], os.path.join(cls.CACHE_DIR, id))

    @classmethod
    def renew_gitRepo(cls, id: str, item: CacheItem):
        from zuu.APP.git import update_repo

        os.makedirs(os.path.join(cls.CACHE_DIR, id), exist_ok=True)
        update_repo(
            path=os.path.join(cls.CACHE_DIR, id),
            url=item["meta"]["url"],
            branch=item["meta"].get("branch", "None"),
        )

    @classmethod
    def get_path(cls, id: str):
        return os.path.join(cls.CACHE_DIR, id)
