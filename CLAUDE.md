# Project context — Rekordbox playlist sync

## Environment
- macOS Apple Silicon
- Rekordbox **7.2.14**
- Python via `uv`
- `pyrekordbox 0.4.4` (PyPI)
- `sqlcipher3` installed via Homebrew

```python
from pyrekordbox import Rekordbox6Database
db = Rekordbox6Database()  # works with RBK7
```

To get the `master.db` path:
```python
from pyrekordbox.config import get_config
db_path = get_config("rekordbox", "db_path")
```

## CLI — `rkb` (entry point `rkb_lib.cli:main`)

Installed via `uv` (see `pyproject.toml`).

### Commands

```
rkb playlists [--apply]   # Sync playlists from structure.toml
rkb genres                # List all genres + mapped/unmapped status
rkb genres --search QUERY # Search a genre in genrefy
rkb genres --interactive  # Interactive mode: rename unmapped genres
```

### `rkb playlists` behavior
- Automatic backup of `master.db` before any write
- Creates a folder/playlist structure based on the **Genre (ID3)** field
- **Clears and repopulates** playlists on every run — fixing a genre in RBK
  then re-running is enough to put everything back in place
- Unmapped genres → `TODO / A Classer`
- Junk genres (URLs, mp3-crazy, etc.) → ignored entirely
- Dry-run by default, `--apply` to write
- **Rekordbox must be closed** before `--apply`

### `rkb genres`
- Displays a table of genres present in the DB with track counts
- Shows which ones are mapped in `structure.toml` and which aren't
- `--interactive`: for each unmapped genre, offers to search genrefy
  and rename the genre in the Rekordbox DB **and** the files' ID3 tags

## Package structure

```
rkb_lib/
  cli.py       — entry point, argparse parsing
  playlist.py  — playlist structure sync
  genres.py    — listing, renaming, genrefy integration
  config.py    — structure.toml loading
```

## Configuration — `structure.toml`

Resolution order:
1. Env var `RKB_STRUCTURE`
2. `./structure.toml` (current directory)
3. `~/.config/rkb-lib/structure.toml`

## Important
These are **regular playlists**, not intelligent playlists.
Creating intelligent playlists programmatically is not supported
by pyrekordbox — don't try.

## Target structure
```
DEEP & ORGANIC
    Deep House
    Afro & Organic House
    Indie Dance & Nu Disco

GROOVE & TECH
    Tech House & Jackin'
    Progressive House
    Future House

MELODIC
    Melodic House
    Melodic Techno
    Future Rave
    Progressive Trance

DARK & DRIVING
    Peak Time Techno
    Raw & Deep Techno
    Hard Techno & Industrial
    Acid & Rave

TRANCE & UPLIFTING
    Uplifting & Main Floor
    Psy-Trance

FESTIVAL
    Big Room & Mainstage
    Hard Dance & Neo Rave
    Hardstyle

BREAKS & BASS
    Breakbeat & UK Bass
    Drum & Bass
    Dubstep & Bass
    Trap & Future Bass

WORLD & GROOVE
    Afro & Latin
    Disco & Funk

TOOLS
    Warm Up
    Transitions
    Closing

TODO
    A Classer   ← unmapped genres, fix manually in RBK then re-run
```

## Design rules
- No duplicate playlists — each genre belongs to exactly one playlist
- Extensible: adding a genre = one line in the TOML
- Genre matching is case-insensitive
