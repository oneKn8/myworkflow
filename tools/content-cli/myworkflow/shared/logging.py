"""Shared Rich console and logging setup."""

from rich.console import Console

console = Console()


def success(msg: str) -> None:
    console.print(f"[green]{msg}[/green]")


def error(msg: str) -> None:
    console.print(f"[red]{msg}[/red]")


def info(msg: str) -> None:
    console.print(f"[dim]{msg}[/dim]")


def warn(msg: str) -> None:
    console.print(f"[yellow]{msg}[/yellow]")
