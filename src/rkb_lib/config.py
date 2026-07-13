import os
import tomllib
from pathlib import Path

_DEFAULT_CONFIG = Path.home() / ".config" / "rkb-lib" / "structure.toml"
_LOCAL_CONFIG = Path.cwd() / "structure.toml"


def find_config() -> Path:
    if env := os.environ.get("RKB_STRUCTURE"):
        p = Path(env)
        if not p.exists():
            raise FileNotFoundError(f"RKB_STRUCTURE={p} not found")
        return p
    if _LOCAL_CONFIG.exists():
        return _LOCAL_CONFIG
    if _DEFAULT_CONFIG.exists():
        return _DEFAULT_CONFIG
    raise FileNotFoundError(
        f"structure.toml not found. Expected at:\n"
        f"  {_DEFAULT_CONFIG}\n"
        f"  {_LOCAL_CONFIG}\n"
        f"Or set RKB_STRUCTURE=<path>"
    )


def load_structure() -> tuple[dict, set]:
    """Returns (structure, ignored_genres)."""
    path = find_config()
    with open(path, "rb") as f:
        data = tomllib.load(f)

    ignored = set(data.get("ignored_genres", {}).get("genres", []))

    structure: dict = {}
    for entry in data.get("playlist", []):
        parts = entry["path"]
        if len(parts) != 2:
            continue
        root, playlist = parts
        structure.setdefault(root, {})[playlist] = entry.get("genres", [])

    return structure, ignored
