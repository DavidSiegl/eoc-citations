# Element of Crime Citations

A small program that scrapes Element of Crime lyrics from **Genius.com** and displays random quotes, intended for use with `hyprlock`.

## Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Harvest the lyrics:
   ```bash
   uv run harvester.py
   ```
   *Note: This will create a `lyrics.json` file. It fetches the song list via the Genius API and then scrapes the lyrics.*

3. Get a random quote:
   ```bash
   uv run quote.py
   ```

## Hyprlock Integration

Add the following to your `hyprlock.conf`:

```ini
label {
    monitor =
    text = cmd[update:0] uv run /path/to/eoc-citations/quote.py
    color = rgba(200, 200, 200, 1.0)
    font_size = 20
    font_family = Noto Sans
    position = 0, 80
    halign = center
    valign = center
}
```
