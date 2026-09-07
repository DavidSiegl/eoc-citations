"""Project Gutenberg: passages from public-domain books. Atomic items.

Talks to gutenberg.org directly - the usual gutendex.com JSON wrapper is not
reliably reachable, so this scrapes the search page and reads the plaintext
cache endpoint instead.
"""

import random
import re

from bs4 import BeautifulSoup

from .base import Candidate, Item, Source, SourceError, Subject, get

BASE = "https://www.gutenberg.org"
MAX_PASSAGES = 300  # per book, keeps the stored file small and varied

_START = re.compile(r"\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*",
                    re.IGNORECASE | re.DOTALL)
_END = re.compile(r"\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*",
                  re.IGNORECASE | re.DOTALL)
_SENTENCE = re.compile(r"(?<=[.!?])\s+")
_ALLCAPS = re.compile(r"^[^a-z]{8,}$")


def extract_passages(text: str, limit: int = MAX_PASSAGES) -> list[str]:
    """Strip the Gutenberg licence wrapper, then sample readable sentences."""
    if m := _START.search(text):
        text = text[m.end():]
    if m := _END.search(text):
        text = text[:m.start()]

    # Paragraphs are blank-line separated; rejoin their internal hard wraps.
    paragraphs = re.split(r"\n\s*\n", text)
    candidates = []
    for para in paragraphs:
        flat = re.sub(r"\s+", " ", para).strip()
        if len(flat) < 60 or _ALLCAPS.match(flat):
            continue  # chapter headings, front matter, transcriber notes
        if flat.startswith(("Produced by", "Transcribed", "[Illustration")):
            continue
        for sentence in _SENTENCE.split(flat):
            sentence = sentence.strip()
            if not (60 <= len(sentence) <= 300):
                continue
            if not sentence[0].isupper() or "_" in sentence:
                continue
            if sentence.count('"') % 2:  # dangling quote from a split dialogue
                continue
            candidates.append(sentence)

    if len(candidates) > limit:
        candidates = random.sample(candidates, limit)
    return candidates


class Gutenberg:
    name = "gutenberg"
    domain = "prose"
    produces_atomic = True

    def search(self, query: str, lang: str = "en") -> list[Candidate]:
        resp = get(f"{BASE}/ebooks/search/", params={"query": query},
                   key="gutenberg", throttle=1.0)
        soup = BeautifulSoup(resp.text, "lxml")
        out = []
        for link in soup.select("li.booklink a.link"):
            href = link.get("href", "")
            m = re.match(r"^/ebooks/(\d+)$", href)
            if not m:
                continue
            title = link.select_one(".title")
            author = link.select_one(".subtitle")
            out.append(Candidate(
                source=self.name, source_id=m.group(1),
                name=(title.get_text(strip=True) if title else query),
                domain=self.domain, lang=lang,
                url=f"{BASE}/ebooks/{m.group(1)}",
                hint=author.get_text(strip=True) if author else "",
            ))
            if len(out) >= 8:
                break
        return out

    def fetch(self, cand: Candidate, progress=None) -> Subject:
        if progress:
            progress(f"downloading ebook {cand.source_id}")
        book_id = cand.source_id
        last_err = None
        for url in (f"{BASE}/cache/epub/{book_id}/pg{book_id}.txt",
                    f"{BASE}/files/{book_id}/{book_id}-0.txt",
                    f"{BASE}/ebooks/{book_id}.txt.utf-8"):
            try:
                resp = get(url, key="gutenberg", throttle=1.0)
            except SourceError as exc:
                last_err = exc
                continue
            resp.encoding = resp.encoding or "utf-8"
            if progress:
                progress("extracting passages")
            passages = extract_passages(resp.text)
            if not passages:
                continue
            return Subject(
                source=self.name, source_id=book_id,
                name=cand.hint or cand.name, domain=self.domain, lang=cand.lang,
                url=cand.url,
                items=[Item(lines=[p], work=cand.name, url=cand.url, atomic=True)
                       for p in passages],
                attribution={"provider": "Project Gutenberg", "url": cand.url,
                             "license": "public domain"},
            )
        raise SourceError(f"could not retrieve ebook {book_id}: {last_err}")


SOURCE = Gutenberg()
