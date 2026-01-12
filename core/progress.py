"""Progress indicators for CLI operations."""

from typing import Optional
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.console import Console

_console = Console()
_verbose_mode = False
_quiet_mode = False


def set_verbose(enabled: bool):
    """Enable/disable verbose mode."""
    global _verbose_mode
    _verbose_mode = enabled


def set_quiet(enabled: bool):
    """Enable/disable quiet mode."""
    global _quiet_mode
    _quiet_mode = enabled


def is_verbose() -> bool:
    """Check if verbose mode is enabled."""
    return _verbose_mode


def is_quiet() -> bool:
    """Check if quiet mode is enabled."""
    return _quiet_mode


def log(message: str, style: Optional[str] = None):
    """Log a message (respects quiet mode)."""
    if not _quiet_mode:
        _console.print(message, style=style)


def log_verbose(message: str):
    """Log a verbose message."""
    if _verbose_mode and not _quiet_mode:
        _console.print(f'[dim]{message}[/dim]', style='dim')


def log_error(message: str):
    """Log an error message."""
    _console.print(f'[red]Error:[/red] {message}', style='red')


def log_success(message: str):
    """Log a success message."""
    if not _quiet_mode:
        _console.print(f'[green]✓[/green] {message}', style='green')


def create_progress(message: str, total: Optional[int] = None) -> Progress:
    """Create a progress indicator."""
    if _quiet_mode:
        return Progress(console=_console, disable=True)
    
    columns = [
        SpinnerColumn(),
        TextColumn('[progress.description]{task.description}'),
    ]
    
    if total:
        columns.extend([
            BarColumn(),
            TextColumn('[progress.percentage]{task.percentage:>3.0f}%'),
        ])
    
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
                    progress.update(task, description=f'[red]Failed: {e}[/red]')
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
                progress.update(task, description=f'[red]Failed: {e}[/red]')
                raise
