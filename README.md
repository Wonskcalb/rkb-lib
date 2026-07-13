# rkb-lib

CLI to manage a Rekordbox library: automatic genre-based playlist sync and tag management.

## Requirements

- macOS Apple Silicon
- Rekordbox 7.x
- Python ≥ 3.13 with [uv](https://docs.astral.sh/uv/)
- `sqlcipher3` installed via Homebrew

## Installation

```bash
uv sync
```

The `rkb` script is installed as an entry point.

## Usage

### Playlists

```bash
# Preview without changing anything (dry-run)
rkb playlists

# Apply (Rekordbox must be closed)
rkb playlists --apply
```

Creates or updates a folder/playlist tree in Rekordbox from each track's **Genre (ID3)** field. A backup of `master.db` is created automatically before any write.

Playlists are **cleared and repopulated** on every run — fixing a genre in Rekordbox then re-running is enough to put everything back in place. Unmapped genres land in `TODO / A Classer`.

### Genres

```bash
# See all genres with mapped/unmapped status
rkb genres

# Search a term in genrefy
rkb genres --search "afro house"

# Interactive mode: rename unmapped genres (DB + ID3 tags)
rkb genres --interactive
```

## Configuration — `structure.toml`

Defines the target tree and the genres associated with each playlist. Resolution order:

1. Env var `RKB_STRUCTURE`
2. `./structure.toml` (current directory)
3. `~/.config/rkb-lib/structure.toml`

Example entry:

```toml
[[playlist]]
path = ["DEEP & ORGANIC", "Deep House"]
genres = ["Deep House", "House - Deep"]
```

Genres listed in `[ignored_genres]` are ignored entirely (junk URLs, samples, etc.).

## Target structure

```
DEEP & ORGANIC        Deep House / Afro & Organic House / Indie Dance & Nu Disco
GROOVE & TECH         Tech House & Jackin' / Progressive House / Future House
MELODIC               Melodic House / Melodic Techno / Future Rave / Progressive Trance
DARK & DRIVING        Peak Time Techno / Raw & Deep Techno / Hard Techno / Acid & Rave
TRANCE & UPLIFTING    Uplifting & Main Floor / Psy-Trance
FESTIVAL              Big Room & Mainstage / Hard Dance & Neo Rave / Hardstyle
BREAKS & BASS         Breakbeat & UK Bass / Drum & Bass / Dubstep & Bass / Trap
WORLD & GROOVE        Afro & Latin / Disco & Funk
TOOLS                 Warm Up / Transitions / Closing
TODO                  A Classer  ← unmapped genres
```
