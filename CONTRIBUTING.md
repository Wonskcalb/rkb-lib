# Contributing

## Setup

```bash
uv sync
```

Requires macOS Apple Silicon, Rekordbox 7.x, and `sqlcipher3` (via Homebrew) — see [README.md](README.md).

## Workflow

1. Fork/branch from `main`.
2. Make your change.
3. Verify locally:
   ```bash
   uv run python -m compileall src
   uv run rkb --help
   ```
4. Open a PR against `main`. CI runs the same checks.

## Guidelines

- Keep `rkb playlists` dry-run-safe by default — no destructive DB writes without `--apply`.
- Playlist name/genre changes in `structure.toml` affect real Rekordbox data on the next `--apply`; call these out explicitly in your PR description.
- No new abstractions or dependencies unless the task needs them.
- Write in English — code, comments, docs, commit messages.
