"""Progress indicators for CLI operations."""

from typing import Optional

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from core.settings import settings

_console = Console()


def is_verbose() -> bool:
    """Check if verbose mode is enabled."""
    return settings.verbose


def is_quiet() -> bool:
    """Check if quiet mode is enabled."""
    return settings.quiet


def log(message: str, style: Optional[str] = None):
    """Log a message (respects quiet mode)."""
    if not settings.quiet:
        _console.print(message, style=style)


def log_verbose(message: str):
    """Log a verbose message."""
    if settings.verbose and not settings.quiet:
        _console.print(f"[dim]{message}[/dim]", style="dim")


def log_error(message: str):
    """Log an error message (always shown, even in quiet mode)."""
    _console.print(f"[red]Error:[/red] {message}", style="red")


def log_success(message: str):
    """Log a success message."""
    if not settings.quiet:
        _console.print(f"[green]\u2713[/green] {message}", style="green")


def create_progress(message: str, total: Optional[int] = None) -> Progress:
    """Create a progress indicator."""
    if settings.quiet:
        return Progress(console=_console, disable=True)

    columns = [
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
    ]

    if total:
        columns.extend(
            [
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            ]
        )

    columns.append(TimeElapsedColumn())

    return Progress(*columns, console=_console)


def with_progress(message: str, fn, *args, **kwargs):
    """Execute function with progress indicator."""
    import asyncio

    if asyncio.iscoroutinefunction(fn):

        async def _async_wrapper():
            with create_progress(message) as progress:
                task = progress.add_task(message, total=None)
                try:
                    result = await fn(*args, **kwargs)
                    progress.update(task, completed=True)
                    return result
                except Exception as e:
                    progress.update(task, description=f"[red]Failed: {e}[/red]")
                    raise

        return asyncio.run(_async_wrapper())
    else:
        with create_progress(message) as progress:
            task = progress.add_task(message, total=None)
            try:
                result = fn(*args, **kwargs)
                progress.update(task, completed=True)
                return result
            except Exception as e:
                progress.update(task, description=f"[red]Failed: {e}[/red]")
                raise
