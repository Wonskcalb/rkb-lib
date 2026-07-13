import os
import subprocess

from pyrekordbox import Rekordbox6Database
from rich import box
from rich.console import Console
from rich.table import Table

from rkb_lib.config import load_structure

console = Console()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_track_path(content) -> str | None:
    try:
        folder = content.FolderPath or ""
        filename = content.FileNameL or getattr(content, "FileName", "") or ""
        if folder and filename:
            return os.path.join(folder, filename)
    except AttributeError:
        pass
    return None


def _update_id3_genre(file_path: str, genre: str) -> bool:
    try:
        from mutagen import File as MutagenFile

        audio = MutagenFile(file_path, easy=True)
        if audio is None:
            return False
        audio["genre"] = [genre]
        audio.save()
        return True
    except Exception as e:
        console.print(
            f"  [yellow]WARN[/] ID3 tag not updated ({os.path.basename(file_path)}): {e}"
        )
        return False


def _get_or_create_rkb_genre(db: Rekordbox6Database, name: str):
    for g in db.get_genre():
        if g.Name.lower() == name.lower():
            return g
    try:
        from pyrekordbox.db6.tables import DjmdGenre

        new_g = DjmdGenre(Name=name)
        db._session.add(new_g)
        db._session.flush()
        return new_g
    except Exception as e:
        raise RuntimeError(f"Cannot create genre '{name}' in Rekordbox: {e}") from e


def rename_genre(
    db: Rekordbox6Database, old_name: str, new_name: str, dry_run: bool = False
) -> int:
    tracks = [
        c
        for c in db.get_content()
        if c.Genre and c.Genre.Name.strip().lower() == old_name.lower()
    ]

    if not tracks:
        console.print(f"  No tracks with genre [bold]{old_name!r}[/].")
        return 0

    if dry_run:
        console.print(
            f"  [dim]DRY-RUN[/] {len(tracks)} tracks: {old_name!r} → {new_name!r}"
        )
        return len(tracks)

    new_genre = _get_or_create_rkb_genre(db, new_name)
    id3_ok = 0
    for track in tracks:
        track.GenreID = new_genre.ID
        path = _get_track_path(track)
        if path and os.path.exists(path):
            if _update_id3_genre(path, new_name):
                id3_ok += 1

    db.commit()
    console.print(
        f"  [green]✓[/] {len(tracks)} tracks renamed: {old_name!r} → [cyan]{new_name!r}[/]"
        f"  [dim](ID3: {id3_ok}/{len(tracks)})[/]"
    )
    return len(tracks)


# ── Genre table helpers ────────────────────────────────────────────────────────


def get_all_genres(
    db: Rekordbox6Database, ignored: set
) -> tuple[dict[str, int], dict[str, list[str]]]:
    counts: dict[str, int] = {}
    examples: dict[str, list[str]] = {}
    for content in db.get_content():
        genre_obj = content.Genre
        if genre_obj is None:
            continue
        name = genre_obj.Name.strip()
        if name in ignored:
            continue
        counts[name] = counts.get(name, 0) + 1
        if len(examples.get(name, [])) < 3:
            title = getattr(content, "Title", None) or getattr(content, "Name", None)
            if title:
                examples.setdefault(name, []).append(title)
    return counts, examples


def get_mapped_genres(structure: dict) -> set[str]:
    mapped: set[str] = set()
    for playlists in structure.values():
        for genres in playlists.values():
            for g in genres:
                mapped.add(g.lower())
    return mapped


# ── Genrefy integration ────────────────────────────────────────────────────────


def search_genrefy(query: str) -> None:
    try:
        subprocess.run(["genrefy"], input=f"{query}\n\n", text=True, check=False)
    except FileNotFoundError:
        console.print(
            "[yellow]genrefy not found.[/] Install it with: "
            "[bold]uv tool install <path-to-genrefy>[/]"
        )


# ── Output ────────────────────────────────────────────────────────────────────


def _print_genre_table(
    genre_counts: dict[str, int], mapped_lower: set
) -> tuple[list, list]:
    unmapped = [
        (n, c) for n, c in genre_counts.items() if n.lower() not in mapped_lower
    ]
    mapped = [(n, c) for n, c in genre_counts.items() if n.lower() in mapped_lower]

    table = Table(box=box.ROUNDED, show_header=True, padding=(0, 1))
    table.add_column("Genre", min_width=30)
    table.add_column("Tracks", justify="right", style="cyan")
    table.add_column("", justify="center", width=4)

    for name, count in sorted(mapped, key=lambda x: x[0].lower()):
        table.add_row(name, str(count), "[green]✓[/]")
    for name, count in sorted(unmapped, key=lambda x: x[0].lower()):
        table.add_row(f"[yellow]{name}[/]", str(count), "[red]✗[/]")

    console.print()
    console.print(table)

    stats = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    stats.add_column(style="dim")
    stats.add_column(justify="right")
    stats.add_row("Mapped", f"[green]{len(mapped)}[/]")
    stats.add_row("Unmapped", f"[red]{len(unmapped)}[/]")
    stats.add_row("Total", f"[bold]{len(genre_counts)}[/]")
    console.print(stats)

    return mapped, unmapped


# ── Command entry point ────────────────────────────────────────────────────────


def run(search: str | None = None, interactive: bool = False):
    try:
        structure, ignored = load_structure()
    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise SystemExit(1)

    with console.status("[dim]Opening Rekordbox database…[/]"):
        try:
            db = Rekordbox6Database()
        except Exception as e:
            console.print(f"[bold red]Error:[/] Cannot open Rekordbox database: {e}")
            raise SystemExit(1)

        genre_counts, genre_examples = get_all_genres(db, ignored)

    if not genre_counts:
        console.print("No genres found in the Rekordbox database.")
        return

    mapped_lower = get_mapped_genres(structure)
    _, unmapped = _print_genre_table(genre_counts, mapped_lower)

    if search:
        console.rule(f"[dim]genrefy search: {search!r}[/]")
        search_genrefy(search)
        return

    if not interactive:
        return

    if not unmapped:
        console.print("\n[green]✓ All genres are mapped.[/]")
        return

    console.print()
    console.print(
        "[bold]Interactive mode[/] — unmapped genres\n"
        "[dim]Enter a genrefy search term, then a new name to rename. "
        "Empty = skip. Ctrl+C = quit.[/]"
    )

    for name, count in sorted(unmapped, key=lambda x: x[0].lower()):
        console.rule(f"[bold cyan]{name}[/] [dim]({count} tracks)[/]")

        examples = genre_examples.get(name, [])
        if examples:
            console.print("  [dim]e.g. " + " · ".join(examples) + "[/]")

        try:
            query = console.input("[bold cyan]  genrefy>[/] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Bye![/]")
            break

        if not query:
            continue

        search_genrefy(query)

        try:
            new_name = console.input(f"[dim]  Rename [bold]{name!r}[/] →[/] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Bye![/]")
            break

        if new_name and new_name != name:
            rename_genre(db, name, new_name, dry_run=False)
