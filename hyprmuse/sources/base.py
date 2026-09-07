"""Shared types and HTTP helpers for quote sources."""

import time
from dataclasses import dataclass, field
from typing import Protocol

import requests

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
TIMEOUT = 20


class SourceError(RuntimeError):
    """A source could not fulfil a search or fetch."""


@dataclass
class Candidate:
    """A subject a source could harvest, before any harvesting happens."""

    source: str
    source_id: str
    name: str
    domain: str
    lang: str = "en"
    url: str = ""
    hint: str = ""  # shown to the user when disambiguating


@dataclass
class Item:
    """One harvested unit: a song, a poem, a quotation, a passage.

    ``atomic`` items are quoted whole (a Wikiquote line, a prose passage).
    Non-atomic items are sliceable: a random window of lines is taken.
    """

    lines: list[str]
    work: str = ""
    url: str = ""
    atomic: bool = False
    note: str = ""  # source citation, e.g. the book a quote came from


@dataclass
class Subject:
    """A harvested subject plus everything needed to attribute it."""

    source: str
    source_id: str
    name: str
    domain: str
    lang: str = "en"
    url: str = ""
    items: list[Item] = field(default_factory=list)
    attribution: dict = field(default_factory=dict)


class Source(Protocol):
    name: str
    domain: str
    produces_atomic: bool

    def search(self, query: str, lang: str) -> list[Candidate]: ...
    def fetch(self, cand: Candidate, progress=None) -> Subject: ...


_LAST_CALL: dict[str, float] = {}


def get(url: str, *, params: dict | None = None, throttle: float = 0.0,
        key: str = "default", headers: dict | None = None) -> requests.Response:
    """GET with a browser UA, a timeout, and optional per-host throttling."""
    if throttle:
        elapsed = time.monotonic() - _LAST_CALL.get(key, 0.0)
        if elapsed < throttle:
            time.sleep(throttle - elapsed)
    hdrs = {"User-Agent": USER_AGENT}
    if headers:
        hdrs.update(headers)
    try:
        resp = requests.get(url, params=params, headers=hdrs, timeout=TIMEOUT)
    except requests.RequestException as exc:
        raise SourceError(f"request to {url} failed: {exc}") from exc
    finally:
        _LAST_CALL[key] = time.monotonic()
    if resp.status_code != 200:
        raise SourceError(f"{url} returned HTTP {resp.status_code}")
    return resp
