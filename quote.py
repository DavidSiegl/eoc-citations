import json
import random
import os
import sys

DATA_FILE = os.path.join(os.path.dirname(__file__), "lyrics.json")


def get_random_quote(num_lines=3):
    if not os.path.exists(DATA_FILE):
        return "No lyrics found. Please execute harvester.py first."

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        return "No data found."

    # Pick a random song
    song_ids = list(data.keys())
    song_id = random.choice(song_ids)
    song = data[song_id]
    lyrics = song["lyrics"]
    title = song["title"]

    lines = [line.strip() for line in lyrics.split("\n") if line.strip()]

    # Filter out very short lines or common filler (like [Chorus])
    # Also filter out Genius-specific metadata like "Contributors"
    filtered_lines = []
    for l in lines:
        l_lower = l.lower()
        if len(l) < 2:
            continue
        if l.startswith("[") and l.endswith("]"):
            continue
        if "contributor" in l_lower:
            continue
        if "you might also like" in l_lower:
            continue
        if "lyrics" in l_lower:
            continue
        if "embed" == l_lower:
            continue
        if l_lower.startswith("refrain"):
            continue
        if l_lower.startswith("strophe"):
            continue

        filtered_lines.append(l)

    if not filtered_lines:
        return f"Element of Crime - {title}"

    if len(filtered_lines) <= num_lines:
        quote = filtered_lines
    else:
        # Pick a starting point
        start_index = random.randint(0, len(filtered_lines) - num_lines)
        quote = filtered_lines[start_index: start_index + num_lines]

    quote_text = "\n".join(quote)
    return f"{quote_text}\n\n— Element of Crime: {title}"


if __name__ == "__main__":
    print(get_random_quote())
