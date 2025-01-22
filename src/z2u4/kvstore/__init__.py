import re
import time
import typing
from masscode.direct import MasscodeApi
from masscode import Models
class _Kvstore:
    def get(self, key : str):
        snippet = None
        try:
            snippet = MasscodeApi.get_snippet(key)
        except Exception:
            snippet = MasscodeApi.snippets(params={"name_like" : key})
            if len(snippet) == 0:
                return None
            snippet = snippet[0]
        if snippet is None:
            return None
        return snippet.content[0]['value']
    
    def set(self, key : str, value : str):
        snippet = self.get(key)
        if snippet is None:
            snippet = MasscodeApi.create_snippet(
                name=key,
                content=[{
                    "language" : "text",
                    "value" : value,
                    "label" : "main"
                }],
                createdAt=int(time.time()),
                updatedAt=int(time.time()),
            )
        else:
            snippet.content[0]['value'] = value
            snippet.updatedAt = int(time.time())
            MasscodeApi.update_snippet(snippet)
        return snippet

    def __getitem__(self, key : str):
        return self.get(key)
    
    def __setitem__(self, key : str, value : str):
        return self.set(key, value)
    

kvstore = _Kvstore()


def parse_document(document: str) -> dict:
    pattern = r'<\$@(\w+)>'
    matches = re.findall(pattern, document)
    allsnippets : typing.List[Models.Snippet] = MasscodeApi.snippets()
    
    for match in matches:
        key = match
        snippet = next((s for s in allsnippets if s["name"] == key), None)
        if snippet is None:
            snippet = next((s for s in allsnippets if key in s["name"]), None)
        
        if snippet is None:
            raise ValueError(f"Key {key} not found in store")
        document = re.sub(r'^//<\$@' + re.escape(key) + '>', f'<$@{key}>', document, flags=re.MULTILINE)
        document = re.sub(r'^#<\$@' + re.escape(key) + '>', f'<$@{key}>', document, flags=re.MULTILINE)
        document = document.replace(f'<$@{key}>', snippet["content"][0]['value'])
        
    return document