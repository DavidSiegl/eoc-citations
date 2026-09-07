"""Pick a random quote across the library, avoiding recent repeats."""

import hashlib
import json
import random
from dataclasses import dataclass

from . import config, library
from .sources.base import Item, Subject


@dataclass
class Pick:
    subject: Subject
    item: Item
    lines: list[str]

    def fingerprint(self) -> str:
        seed = f"{self.subject.source}:{self.subject.source_id}:" + "|".join(self.lines)
        return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]


def _load_recent() -> list[str]:
    try:
        return json.loads(config.RECENT_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def _save_recent(seen: list[str], keep: int) -> None:
    try:
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        config.RECENT_FILE.write_text(json.dumps(seen[-keep:]), encoding="utf-8")
    except OSError:
        pass  # a read-only home must not break the lockscreen


def candidates(cfg: dict, *, subject: str = "", domain: str = "",
               source: str = "") -> list[Subject]:
    """Stored subjects, minus those disabled in config or excluded by filters."""
    subjects = library.load_all()
    out = []
    for subj in subjects:
        settings = cfg.get("subjects", {}).get(
            library.subject_key(subj.source, subj.source_id), {})
        if settings.get("enabled") is False:
            continue
        if domain and subj.domain != domain:
            continue
        if source and subj.source != source:
            continue
        if subject and subject.lower() not in subj.name.lower() \
                and subject != library.subject_key(subj.source, subj.source_id):
            continue
        if subj.items:
            out.append(subj)
    return out


def _weight(subj: Subject, cfg: dict) -> float:
    settings = cfg.get("subjects", {}).get(
        library.subject_key(subj.source, subj.source_id), {})
    base = float(settings.get("weight", 1.0))
    # "quote" weighting makes every stored quote equally likely, so prolific
    # subjects dominate; "subject" (the default) gives each subject equal say.
    return base * len(subj.items) if cfg.get("weighting") == "quote" else base


def _extract(item: Item, num_lines: int, rng: random.Random) -> list[str]:
    lines = [ln for ln in item.lines if ln.strip()]
    if not lines:
        return []
    if item.atomic or len(lines) <= num_lines:
        return lines
    start = rng.randint(0, len(lines) - num_lines)
    return lines[start:start + num_lines]


def pick(cfg: dict, *, num_lines: int, subject: str = "", domain: str = "",
         source: str = "", seed: int | None = None) -> Pick | None:
    """Choose one quote, retrying briefly to avoid a recently shown one."""
    pool = candidates(cfg, subject=subject, domain=domain, source=source)
    if not pool:
        return None
    rng = random.Random(seed)
    recent = _load_recent()
    keep = int(cfg.get("avoid_repeats", 20))
    weights = [_weight(s, cfg) for s in pool]
    if sum(weights) <= 0:
        weights = [1.0] * len(pool)

    chosen = None
    for _ in range(40):
        subj = rng.choices(pool, weights=weights, k=1)[0]
        item = rng.choice(subj.items)
        lines = _extract(item, num_lines, rng)
        if not lines:
            continue
        chosen = Pick(subj, item, lines)
        if keep <= 0 or chosen.fingerprint() not in recent:
            break

    if chosen and keep > 0 and seed is None:
        _save_recent(recent + [chosen.fingerprint()], keep)
    return chosen
