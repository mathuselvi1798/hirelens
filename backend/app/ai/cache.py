"""Result cache keyed on content, not on request identity.

AI calls are the only expensive operation in this application, in both latency
and money. Re-analyzing an unchanged document with an unchanged prompt should
never cost a second call, so the key is
`(document content hash, module id, prompt version, extra inputs hash)`.

Bumping a module's `prompt_version` invalidates its cache automatically - which
is exactly what you want while iterating on a prompt.
"""
import hashlib
from collections import OrderedDict
from typing import Any


def build_cache_key(
    *, content_hash: str, module_id: str, prompt_version: str, extra: str = ""
) -> str:
    extra_hash = hashlib.sha256(extra.encode("utf-8")).hexdigest()[:16] if extra else "none"
    return f"{module_id}:{prompt_version}:{content_hash[:32]}:{extra_hash}"


class InMemoryResultCache:
    def __init__(self, max_items: int = 500) -> None:
        self._items: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._max_items = max_items

    def get(self, key: str) -> dict[str, Any] | None:
        value = self._items.get(key)
        if value is not None:
            self._items.move_to_end(key)
        return value

    def set(self, key: str, value: dict[str, Any]) -> None:
        self._items[key] = value
        self._items.move_to_end(key)
        while len(self._items) > self._max_items:
            self._items.popitem(last=False)

    def clear(self) -> None:
        self._items.clear()
