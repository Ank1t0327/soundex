# Soundex

A minimal, keyboard-driven desktop app for searching and streaming movies and TV shows directly from the IMDb suggestion API. Built with Python and Tkinter — zero dependencies beyond the standard library.

---

## Features

- **Live search** — Queries the IMDb suggestion API as you type, with 300ms debounce and a braille spinner animation while loading.
- **Movie & TV support** — Detects series vs. movie automatically. For TV shows, exposes season and episode number inputs before playback.
- **One-click streaming** — Opens the selected title in fullscreen/kiosk mode on Brave, Chrome, Chromium, or Firefox. Falls back to `xdotool` F11 for any other browser.
- **Trailer search** — Launches a YouTube search for the official trailer directly in the browser.
- **Watch List** — Save titles to watch later. Persisted across sessions. Duplicates are blocked.
- **History** — Automatically tracks the last 20 played titles. Clickable entries reload any previous selection. Full "Clear All" option included.
- **Poster thumbnails** — Fetches and displays cover art via the `wsrv.nl` image proxy, loaded in a background thread so the UI never blocks.
- **Animated buttons** — Custom `RoundedButton` canvas widget with smooth RGB color interpolation on hover and click.
- **Dark theme** — Monospace (`Courier New`) UI throughout, `#121212` base with `#4a90e2` accent.

---

## Requirements

- Python 3.x (standard library only — `tkinter`, `urllib`, `json`, `threading`, `subprocess`, `webbrowser`, `re`, `shutil`, `time`, `os`)
- A supported browser: Brave, Google Chrome, Chromium, or Firefox
- Linux desktop environment (X11/Wayland)

---

## Installation

```bash
# Clone or download the project
git clone <repo-url>
cd soundex

# Make the script executable
chmod +x soundex.py

# Run it
python3 soundex.py
```

### Optional: Add a desktop launcher

Copy the included `.desktop` file to your applications directory and update the `Exec` path to match your installation location:

```bash
# Edit the path inside soundex.desktop first, then:
cp soundex.desktop ~/.local/share/applications/
```

The app will then appear in your application menu under **AudioVideo / Player**.

---

## Usage

1. Start typing a movie or show title in the search bar.
2. Select a result from the dropdown (mouse or arrow keys + Enter).
3. A preview appears with the poster, title, year, and cast info.
4. For TV shows, set the season and episode numbers.
5. Hit **PLAY** to stream, **TRAILER** to open a YouTube trailer search, or **[+] LATER** to add to your Watch List.
6. Access your **Watch List** and **History** from the bottom navigation bar.

---

## Data Storage

User data is saved locally at `~/.local/share/soundex/`:

| File | Contents |
|---|---|
| `history.json` | Last 20 played titles |
| `watchlist.json` | Saved watch-later titles |

---

## Project Structure

```
soundex/
├── soundex.py          # Main application
├── soundex.desktop     # Linux desktop entry
├── test_popup.py       # Test: scrollable list popup with data
└── test_empty.py       # Test: empty state popup
```

---

## Notes

- Streaming uses [playimdb.com](https://www.playimdb.com) with the IMDb title ID.
- Poster images are proxied through [wsrv.nl](https://wsrv.nl) to avoid direct CDN restrictions.
- The canvas scroll region uses a fixed width (`340px`) to prevent infinite layout loops on some Linux window managers.
