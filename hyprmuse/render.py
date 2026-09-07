"""Format a pick for display: wrap, cap, attribute."""

import textwrap

from .select import Pick

DASH = "—"


def wrap(lines: list[str], width: int) -> list[str]:
    """Wrap each line to width, preserving line breaks that are already there.

    Verse and lyric line breaks are meaningful, so they are kept; only lines
    that genuinely overflow (prose quotations) get folded.
    """
    out: list[str] = []
    for line in lines:
        if width <= 0 or len(line) <= width:
            out.append(line)
        else:
            out.extend(textwrap.wrap(line, width=width) or [line])
    return out


def attribution(pick: Pick) -> str:
    who = pick.subject.name
    work = pick.item.work.strip()
    return f"{DASH} {who}: {work}" if work else f"{DASH} {who}"


def render(pick: Pick, *, width: int = 60, max_lines: int = 6,
           show_note: bool = False) -> str:
    body = wrap(pick.lines, width)
    if max_lines > 0 and len(body) > max_lines:
        body = body[:max_lines]
    parts = ["\n".join(body), "", attribution(pick)]
    if show_note and pick.item.note:
        parts.extend(wrap([pick.item.note], width))
    return "\n".join(parts)
