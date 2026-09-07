#!/usr/bin/env python3
"""Compatibility shim: `quote.py` still prints a random quote.

Kept so an existing hyprlock.conf pointing at this file keeps working.
Prefer the installed command: `hyprmuse quote`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hyprmuse.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(["quote", *sys.argv[1:]]))
