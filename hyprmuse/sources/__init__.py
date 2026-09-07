"""Registry of quote sources."""

from . import genius, gutenberg, poetrydb, wikiquote
from .base import Candidate, Item, Source, SourceError, Subject

REGISTRY: dict[str, Source] = {
    s.SOURCE.name: s.SOURCE for s in (genius, wikiquote, poetrydb, gutenberg)
}

# Order tried when the user does not name a source explicitly. Wikiquote first:
# it has the broadest subject coverage across every domain.
AUTO_ORDER = ["wikiquote", "genius", "poetrydb", "gutenberg"]


def get_source(name: str) -> Source:
    try:
        return REGISTRY[name]
    except KeyError:
        raise SourceError(
            f"unknown source '{name}' (have: {', '.join(sorted(REGISTRY))})"
        ) from None


__all__ = ["REGISTRY", "AUTO_ORDER", "get_source", "Candidate", "Item",
           "Source", "SourceError", "Subject"]
