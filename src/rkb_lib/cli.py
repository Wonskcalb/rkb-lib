import sys

from rich.console import Console

console = Console()

HELP = """[bold]rkb[/] — Rekordbox Library Manager

[bold yellow]Usage:[/]
  [cyan]rkb playlists[/]                  Dry run: preview the structure (no writes)
  [cyan]rkb playlists[/] [yellow]--apply[/]           Apply changes (Rekordbox must be closed)
  [cyan]rkb genres[/]                     List all genres and their mapping status
  [cyan]rkb genres[/] [yellow]--search[/] [green]<query>[/]        Search a genre in genrefy
  [cyan]rkb genres[/] [yellow]--interactive[/]         Interactive mode: rename unmapped genres
  [cyan]rkb --help[/]                     Show this help

[bold yellow]Examples:[/]
  [dim]rkb playlists[/]
  [dim]rkb playlists --apply[/]
  [dim]rkb genres[/]
  [dim]rkb genres --search "tech house"[/]
  [dim]rkb genres --interactive[/]

[bold yellow]Config:[/]
  Structure: [dim]$RKB_STRUCTURE[/] or [dim]./structure.toml[/] or [dim]~/.config/rkb-lib/structure.toml[/]
"""


def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h", "help"):
        console.print(HELP)
        raise SystemExit(0 if args else 1)

    if args[0] == "playlists":
        from rkb_lib.playlist import run

        run(dry_run="--apply" not in args)
        return

    if args[0] == "genres":
        interactive = "--interactive" in args
        search = None
        if "--search" in args:
            idx = args.index("--search")
            if idx + 1 >= len(args):
                console.print(
                    "[bold red]Usage:[/] rkb genres --search [green]<query>[/]"
                )
                raise SystemExit(1)
            search = args[idx + 1]
        from rkb_lib.genres import run

        run(search=search, interactive=interactive)
        return

    console.print(f"[bold red]Unknown command:[/] {args[0]!r}\n")
    console.print(HELP)
    raise SystemExit(1)
