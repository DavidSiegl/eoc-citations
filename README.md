# hyprmuse

Random quotes from musicians, literary authors, poets and public-domain books,
for your `hyprlock` screen.

Name a subject, hyprmuse harvests them from a fitting source into a local
library, and prints a random quote on demand. Everything is stored offline, so
the lockscreen never waits on the network.

## Sources

| Source | Domain | Covers | Licence |
|---|---|---|---|
| `wikiquote` | quotations | authors, philosophers, scientists, films, TV, proverbs — any language edition | CC BY-SA |
| `genius` | music | song lyrics for any artist | scraped, personal use |
| `poetrydb` | poetry | ~130 classic poets, full poems | public domain |
| `gutenberg` | prose | passages from public-domain books | public domain |

Sources fall into two kinds. **Sliceable** items (lyrics, poems) are quoted as a
random window of consecutive lines. **Atomic** items (a Wikiquote quotation, a
prose passage) are quoted whole and word-wrapped.

## Setup

```bash
uv sync
```

Import an existing `lyrics.json` from the old eoc-citations layout, if you have one:

```bash
uv run hyprmuse migrate lyrics.json
```

## Usage

```bash
# add subjects — omit --source to search every source and pick from a list
uv run hyprmuse add "Element of Crime" --source genius
uv run hyprmuse add "Ingeborg Bachmann" --source wikiquote --lang de
uv run hyprmuse add "Emily Dickinson" --source poetrydb
uv run hyprmuse add "Frankenstein" --source gutenberg

uv run hyprmuse search "Nietzsche" --lang de   # look without harvesting
uv run hyprmuse list                           # what's stored
uv run hyprmuse update --all                   # re-harvest everything
uv run hyprmuse remove "genius:342499"

uv run hyprmuse quote                          # a random quote
uv run hyprmuse quote --domain poetry --width 50
uv run hyprmuse quote --source wikiquote --note
uv run hyprmuse quote --seed 42                # deterministic
```

`--lang` selects the Wikiquote language edition (`de`, `en`, `fr`, …). Harvesting
is throttled and cached; `add` is the slow step, `quote` reads only local files.

## Hyprlock integration

```ini
label {
    monitor =
    text = cmd[update:0] /path/to/hyprmuse/.venv/bin/hyprmuse quote --width 60
    color = rgba(200, 200, 200, 1.0)
    font_size = 20
    font_family = Noto Sans
    position = 0, 80
    halign = center
    valign = center
}
```

`quote.py` is kept as a compatibility shim, so an existing config pointing at
`/path/to/hyprmuse/quote.py` keeps working — only the directory name changed.

## Configuration

Optional, at `~/.config/hyprmuse/config.toml`:

```toml
[quote]
lines = 3           # lines taken from sliceable items
width = 60          # wrap width, 0 disables wrapping
max_lines = 6       # hard cap after wrapping
weighting = "subject"  # "subject" = every subject equally likely
                       # "quote"   = every quote equally likely
avoid_repeats = 20  # don't repeat within the last N quotes

# per-subject overrides, keyed as shown by `hyprmuse list`
[subjects."genius:342499"]
weight = 2.0
enabled = true
```

`weighting = "subject"` is the default so a 162-song band does not drown out an
author with nine quotes.

## Storage

```
~/.local/share/hyprmuse/subjects/*.json   one file per subject
~/.local/share/hyprmuse/recent.json       recently shown, for repeat avoidance
~/.config/hyprmuse/config.toml            optional settings
```

Harvested text lives outside the repository, so scraped content stays out of git.
