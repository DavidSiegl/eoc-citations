"""The source registry contract every adapter must satisfy."""

import pytest

from hyprmuse.sources import AUTO_ORDER, REGISTRY, get_source
from hyprmuse.sources.base import SourceError


def test_every_source_is_in_the_auto_order():
    assert set(AUTO_ORDER) == set(REGISTRY)


@pytest.mark.parametrize("name", sorted(REGISTRY))
def test_adapter_exposes_the_protocol(name):
    src = REGISTRY[name]
    assert src.name == name
    assert isinstance(src.domain, str) and src.domain
    assert isinstance(src.produces_atomic, bool)
    assert callable(src.search) and callable(src.fetch)


def test_domains_are_distinct():
    domains = [s.domain for s in REGISTRY.values()]
    assert len(domains) == len(set(domains))


def test_get_source_resolves_and_rejects():
    assert get_source("genius").name == "genius"
    with pytest.raises(SourceError, match="unknown source"):
        get_source("nope")
