import shutil
from datetime import datetime
from pathlib import Path

from pyrekordbox import Rekordbox6Database
from pyrekordbox.config import get_config
from rich.console import Console
from rich.panel import Panel

from rkb_lib.config import load_structure

console = Console()

TODO_FOLDER = "TODO"
TODO_PLAYLIST = "A Classer"


def backup_database(dry_run: bool) -> Path | None:
    db_path = get_config("rekordbox7", "db_path")

    if not db_path.exists():
        console.print(f"[bold red]Error:[/] master.db not found: {db_path}")
        raise SystemExit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"master_backup_{timestamp}.db"

    if dry_run:
        console.print(f"[dim]DRY-RUN[/] Backup that would be created: {backup_path}")
        return None

    shutil.copy2(db_path, backup_path)
    console.print(f"[green]✓[/] Backup created: [dim]{backup_path}[/]")
    return backup_path


def _find_folder(db: Rekordbox6Database, name: str) -> object | None:
    for pl in db.get_playlist():
        if pl.Name == name and pl.Attribute == 1:
            return pl
    return None


def _find_playlist(db: Rekordbox6Database, name: str, parent=None) -> object | None:
    parent_id = parent.ID if parent else None
    for pl in db.get_playlist():
        if pl.Name == name and pl.Attribute == 0:
            if parent_id is None or pl.ParentID == parent_id:
                return pl
    return None


def _get_or_create_folder(
    db: Rekordbox6Database, name: str, parent=None, dry_run: bool = False
):
    existing = _find_folder(db, name)
    if existing:
        return existing
    if dry_run:
        console.print(f"  [dim]DRY-RUN[/] Would create folder: [bold]{name!r}[/]")
        return None
    folder = db.create_playlist_folder(name, parent=parent)
    console.print(f"  [blue]✓[/] Folder created: [bold]{name!r}[/]")
    return folder


def _clear_playlist(db: Rekordbox6Database, playlist) -> int:
    entries = db.get_playlist_entries(playlist)
    count = len(entries)
    for entry in entries:
        db.remove_from_playlist(playlist, entry)
    return count


def _get_or_reset_playlist(
    db: Rekordbox6Database, name: str, parent, dry_run: bool
) -> tuple[object | None, bool]:
    existing = _find_playlist(db, name, parent)
    if dry_run:
        return None, False
    if existing:
        removed = _clear_playlist(db, existing)
        if removed:
            console.print(f"  [dim]reset[/] {name!r} — {removed} tracks removed")
        return existing, True
    playlist = db.create_playlist(name, parent=parent)
    return playlist, False


def build_genre_index(db: Rekordbox6Database, ignored: set) -> dict[str, list]:
    index: dict[str, list] = {}
    for content in db.get_content():
        genre_obj = content.Genre
        if genre_obj is None:
            continue
        genre_name = genre_obj.Name.strip()
        if genre_name in ignored:
            continue
        key = genre_name.lower()
        index.setdefault(key, []).append(content)
    return index


def find_tracks_for_genres(genre_index: dict, genres: list[str]) -> list:
    tracks = []
    seen_ids: set = set()
    for g in genres:
        for track in genre_index.get(g.lower(), []):
            if track.ID not in seen_ids:
                tracks.append(track)
                seen_ids.add(track.ID)
    return tracks


def get_unmapped_tracks(genre_index: dict, structure: dict) -> tuple[list, list]:
    all_mapped: set = set()
    for playlists in structure.values():
        for genres in playlists.values():
            for g in genres:
                all_mapped.add(g.lower())

    tracks = []
    seen_ids: set = set()
    unmapped_genres = []
    for key, items in genre_index.items():
        if key not in all_mapped:
            unmapped_genres.append(items[0].Genre.Name)
            for track in items:
                if track.ID not in seen_ids:
                    tracks.append(track)
                    seen_ids.add(track.ID)

    return tracks, unmapped_genres


def create_structure(db: Rekordbox6Database, dry_run: bool):
    structure, ignored = load_structure()

    console.print()

    with console.status("[dim]Scanning library…[/]"):
        genre_index = build_genre_index(db, ignored)

    total_indexed = sum(len(v) for v in genre_index.values())
    console.print(f"[dim]{total_indexed} tracks across {len(genre_index)} distinct genres.[/]\n")

    total_tracks_added = 0

    for root_name, playlists in structure.items():
        console.print(f"[bold cyan]{root_name}[/]")
        root_folder = _get_or_create_folder(db, root_name, parent=None, dry_run=dry_run)

        for playlist_name, genres in playlists.items():
            if root_name == TODO_FOLDER and playlist_name == TODO_PLAYLIST:
                continue

            tracks = find_tracks_for_genres(genre_index, genres)
            genres_str = ", ".join(genres) if genres else "(empty)"

            if dry_run:
                tag = "[yellow]empty[/]  " if not tracks else "         "
                console.print(
                    f"  {tag} {playlist_name} "
                    f"[cyan]{len(tracks)} tracks[/]"
                    f"  [dim]← [{genres_str}][/]"
                )
                continue

            playlist, _ = _get_or_reset_playlist(db, playlist_name, root_folder, dry_run=False)
            for track in tracks:
                db.add_to_playlist(playlist, track)

            total_tracks_added += len(tracks)
            console.print(f"  [green]✓[/] {playlist_name} — [cyan]{len(tracks)} tracks[/]")

        console.print()

    unmapped_tracks, unmapped_genres = get_unmapped_tracks(genre_index, structure)

    if dry_run:
        console.print(f"[bold cyan]{TODO_FOLDER}[/]")
        console.print(f"  {TODO_PLAYLIST} — [cyan]{len(unmapped_tracks)} tracks[/] unmapped")
        if unmapped_genres:
            console.print(f"\n  [yellow]Unmapped genres ({len(unmapped_genres)}):[/]")
            for g in sorted(unmapped_genres):
                n = len(genre_index.get(g.lower(), []))
                console.print(f"    • [yellow]{g!r}[/] [dim]({n} tracks)[/]")
        console.print("\n[dim]Dry run — no changes made. Run with [bold]--apply[/] to apply.[/]")
        return

    todo_folder = _get_or_create_folder(db, TODO_FOLDER, parent=None, dry_run=False)
    todo_playlist, _ = _get_or_reset_playlist(db, TODO_PLAYLIST, todo_folder, dry_run=False)
    for track in unmapped_tracks:
        db.add_to_playlist(todo_playlist, track)
    total_tracks_added += len(unmapped_tracks)
    console.print(f"[bold cyan]{TODO_FOLDER}[/]")
    console.print(
        f"  [green]✓[/] {TODO_PLAYLIST} — "
        f"[cyan]{len(unmapped_tracks)} tracks[/] "
        f"[dim]({len(unmapped_genres)} unmapped genres)[/]"
    )

    db.commit()
    console.print(f"\n[bold green]✓ Done.[/] {total_tracks_added} tracks distributed.")


def run(dry_run: bool = True):
    if dry_run:
        console.print(Panel(
            "[bold]DRY RUN[/] — no changes will be made\n"
            "[dim]Run with [bold]--apply[/] to apply.[/]",
            border_style="dim",
            expand=False,
        ))
    else:
        console.print(Panel(
            "[bold red]APPLY MODE[/] — Rekordbox must be [bold]CLOSED[/]",
            border_style="red",
            expand=False,
        ))

    backup_database(dry_run)

    with console.status("[dim]Opening Rekordbox database…[/]"):
        try:
            db = Rekordbox6Database()
        except Exception as e:
            console.print(f"[bold red]Error:[/] Cannot open Rekordbox database: {e}")
            raise SystemExit(1)

    create_structure(db, dry_run)
