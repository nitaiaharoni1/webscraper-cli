"""Unified output module for all CLI commands."""

import csv
import json
import sys
from typing import Any, Dict, List, Optional

from core.settings import settings


def output(data: Any, format: Optional[str] = None) -> None:
    """Output data in the specified format, respecting quiet mode."""
    if settings.quiet:
        return

    fmt = format or settings.format

    if fmt == "csv":
        if isinstance(data, list) and data and isinstance(data[0], dict):
            _output_csv(data)
        elif isinstance(data, dict):
            _output_csv([data])
        else:
            _output_json(data)
    elif fmt == "table":
        if isinstance(data, list) and data and isinstance(data[0], dict):
            _output_table(data)
        else:
            _output_json(data)
    elif fmt == "plain":
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"{key}: {value}")
        elif isinstance(data, list):
            print("\n".join(str(item) for item in data))
        else:
            print(str(data))
    else:
        _output_json(data)


def output_json(data: Any) -> None:
    """Output JSON data, respecting quiet mode."""
    if settings.quiet:
        return
    print(json.dumps(data, indent=2))


def output_text(text: str) -> None:
    """Output plain text, respecting quiet mode."""
    if settings.quiet:
        return
    print(text)


def _output_json(data: Any) -> None:
    """Internal JSON output."""
    print(json.dumps(data, indent=2))


def _output_csv(data: List[Dict[str, Any]]) -> None:
    """Output list of dicts as CSV."""
    if not data:
        return
    fieldnames = list(dict.fromkeys(k for row in data for k in row))
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, restval="")
    writer.writeheader()
    writer.writerows(data)


def _output_table(data: List[Dict[str, Any]]) -> None:
    """Output list of dicts as Rich table."""
    if not data:
        return
    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(show_header=True, header_style="bold magenta")

    all_keys = list(dict.fromkeys(k for row in data for k in row))
    for key in all_keys:
        table.add_column(key)

    for row in data:
        table.add_row(*[str(row.get(key, "")) for key in all_keys])

    console.print(table)
