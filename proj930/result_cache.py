#!/usr/bin/env python3
"""Thread-safe lokalni cache za privremene MIDI rezultate."""

from __future__ import annotations

import re
import secrets
import threading
import time
from collections import OrderedDict
from pathlib import Path


class ResultCache:
    def __init__(self, limit=10, max_bytes=128_000_000, ttl_seconds=3600):
        self.limit = limit
        self.max_bytes = max_bytes
        self.ttl_seconds = ttl_seconds
        self._items = OrderedDict()
        self._lock = threading.Lock()

    def _prune(self, now):
        expired = [key for key, item in self._items.items() if now - item["created"] > self.ttl_seconds]
        for key in expired:
            self._items.pop(key, None)
        while len(self._items) > self.limit or sum(len(item["midi"]) for item in self._items.values()) > self.max_bytes:
            self._items.popitem(last=False)

    def put(self, midi, report, file_name, suffix="OPT", metadata=None):
        token = secrets.token_urlsafe(18)
        stem = re.sub(r"[^A-Za-z0-9_-]+", "_", Path(file_name).stem)[:48] or "result"
        with self._lock:
            now = time.time()
            self._prune(now)
            self._items[token] = {
                "midi": midi, "report": report, "fileName": f"{stem}_{suffix}.mid",
                "created": now, "metadata": metadata or {},
            }
            self._items.move_to_end(token)
            self._prune(now)
        return token

    def get(self, token):
        with self._lock:
            now = time.time()
            self._prune(now)
            item = self._items.get(token)
            if not item:
                return None
            self._items.move_to_end(token)
            return item

    def summary(self):
        with self._lock:
            self._prune(time.time())
            return {"items": len(self._items), "bytes": sum(len(item["midi"]) for item in self._items.values()),
                    "limit": self.limit, "maxBytes": self.max_bytes, "ttlSeconds": self.ttl_seconds}