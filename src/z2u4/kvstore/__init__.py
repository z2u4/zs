import os
from zuu.STRUCT.dict_with_autosave import DictWithAutosave
import re

USRPATH = os.path.join(os.path.expanduser("~"), ".z2u4", "kvstore")
os.makedirs(USRPATH, exist_ok=True)

kvstore = DictWithAutosave(os.path.join(USRPATH, "kvstore.json"))


def parse_document(document: str, store : dict = kvstore) -> dict:
    pattern = r'<\$@(\w+)>'
    matches = re.findall(pattern, document)
    for match in matches:
        key = match
        value = store.get(key, None)
        if value is None:
            raise ValueError(f"Key {key} not found in store")
        document = document.replace(f'<$@{key}>', value)
    return document