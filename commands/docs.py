"""Documentation and help commands."""

from typing import Optional

import typer

from core.output import output_json
from core.registry import (
    COMMAND_REGISTRY,
    get_all_commands,
    get_command_by_name,
    get_commands_by_category,
    get_total_command_count,
)
from core.settings import settings

app = typer.Typer()


@app.command()
def commands(
    category: Optional[str] = typer.Option(None, help="Filter by category"),
    format: Optional[str] = typer.Option(None, help="Output format: json, table, markdown (overrides global)"),
):
    """List all available commands with descriptions and examples."""
    output_format = format or settings.format

    if category:
        if category not in COMMAND_REGISTRY:
            output_json({"error": f"Category not found: {category}"})
            return
        commands_list = get_commands_by_category(category)
        category_data = COMMAND_REGISTRY[category]
    else:
        commands_list = get_all_commands()
        category_data = None

    if output_format == "json":
        result = {
            "tool": "webscraper-cli",
            "version": "1.0.0",
            "total_commands": get_total_command_count(),
        }

        if category:
            result["category"] = {
                "name": category,
                "description": category_data["description"],
                "commands": commands_list,
            }
        else:
            result["categories"] = []
            for cat_name, cat_data in COMMAND_REGISTRY.items():
                result["categories"].append(
                    {
                        "name": cat_name,
                        "description": cat_data["description"],
                        "commands": list(cat_data["commands"].values()),
                    }
                )

        output_json(result)

    elif output_format == "table":
        from rich.console import Console
        from rich.table import Table

        console = Console()

        if category:
            table = Table(title=f"Commands: {category}", show_header=True, header_style="bold magenta")
            table.add_column("Command", style="cyan")
            table.add_column("Description", style="white")
            table.add_column("Example", style="dim")

            for cmd in commands_list:
                table.add_row(cmd["full_name"], cmd["description"], cmd["example"])
            console.print(table)
        else:
            for cat_name, cat_data in COMMAND_REGISTRY.items():
                table = Table(title=f"Category: {cat_name}", show_header=True, header_style="bold magenta")
                table.add_column("Command", style="cyan", width=30)
                table.add_column("Description", style="white", width=50)
                table.add_column("Example", style="dim", width=60)

                for cmd in cat_data["commands"].values():
                    table.add_row(cmd["full_name"], cmd["description"], cmd["example"])
                console.print(table)
                console.print()

    elif output_format == "markdown":
        if category:
            print(f"# {category.title()} Commands\n")
            print(f"{COMMAND_REGISTRY[category]['description']}\n")
            print("| Command | Description | Example |")
            print("|---------|-------------|---------|")
            for cmd in commands_list:
                print(f"| `{cmd['full_name']}` | {cmd['description']} | `{cmd['example']}` |")
        else:
            print("# Web Scraper CLI Commands\n")
            print(f"Total commands: {get_total_command_count()}\n")
            for cat_name, cat_data in COMMAND_REGISTRY.items():
                print(f"## {cat_name.title()}\n")
                print(f"{cat_data['description']}\n")
                print("| Command | Description | Example |")
                print("|---------|-------------|---------|")
                for cmd in cat_data["commands"].values():
                    print(f"| `{cmd['full_name']}` | {cmd['description']} | `{cmd['example']}` |")
                print()

    else:  # plain
        if category:
            print(f"{category.title()} Commands:")
            print(f"{COMMAND_REGISTRY[category]['description']}\n")
            for cmd in commands_list:
                print(f"  {cmd['full_name']}")
                print(f"    {cmd['description']}")
                print(f"    Example: {cmd['example']}\n")
        else:
            print(f"Web Scraper CLI - {get_total_command_count()} commands\n")
            for cat_name, cat_data in COMMAND_REGISTRY.items():
                print(f"{cat_name.title()}: {cat_data['description']}")
                for cmd in cat_data["commands"].values():
                    print(f"  {cmd['full_name']}: {cmd['description']}")
                print()


@app.command()
def help(
    command: Optional[str] = typer.Argument(None, help='Command name (e.g., "navigate goto" or "api fetch")'),
    category: Optional[str] = typer.Option(None, help="Show all commands in a category"),
):
    """Show detailed help for a command or category."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text

    console = Console()

    if category:
        if category not in COMMAND_REGISTRY:
            console.print(f"[red]Error:[/red] Category not found: {category}")
            console.print(f"\nAvailable categories: {', '.join(COMMAND_REGISTRY.keys())}")
            return

        cat_data = COMMAND_REGISTRY[category]
        console.print(f"\n[bold cyan]Category:[/bold cyan] {category.title()}")
        console.print(f"[dim]{cat_data['description']}[/dim]\n")

        for cmd in cat_data["commands"].values():
            console.print(
                Panel(
                    f"[bold]{cmd['full_name']}[/bold]\n\n"
                    f"{cmd['description']}\n\n"
                    f"[bold]Usage:[/bold] {cmd['usage']}\n"
                    f"[bold]Example:[/bold] [dim]{cmd['example']}[/dim]",
                    title=cmd["full_name"],
                    border_style="blue",
                )
            )
            console.print()
        return

    if not command:
        console.print("[bold]Usage:[/bold] cli.py help <command>")
        console.print("\n[bold]Examples:[/bold]")
        console.print("  cli.py help 'navigate goto'")
        console.print("  cli.py help 'api fetch'")
        console.print("  cli.py help --category navigation")
        console.print("\n[bold]Or use:[/bold] cli.py commands --format table")
        return

    cmd_data = get_command_by_name(command)

    if not cmd_data:
        # Try to find partial matches
        matches = []
        for cmd in get_all_commands():
            if command.lower() in cmd["full_name"].lower():
                matches.append(cmd["full_name"])

        if matches:
            console.print(f"[yellow]Command '{command}' not found. Did you mean:[/yellow]")
            for match in matches[:5]:
                console.print(f"  cli.py help '{match}'")
        else:
            console.print(f"[red]Error:[/red] Command not found: {command}")
            console.print("\nUse 'cli.py commands' to see all available commands.")
        return

    # Format help in brew-style
    help_text = Text()
    help_text.append("NAME\n", style="bold")
    help_text.append(f"    cli.py {cmd_data['full_name']} - {cmd_data['description']}\n\n")

    help_text.append("SYNOPSIS\n", style="bold")
    help_text.append(f"    {cmd_data['usage']}\n\n")

    help_text.append("DESCRIPTION\n", style="bold")
    help_text.append(f"    {cmd_data['description']}\n\n")

    help_text.append("EXAMPLES\n", style="bold")
    help_text.append(f"    # {cmd_data['description']}\n")
    help_text.append(f"    {cmd_data['example']}\n\n")

    # Find related commands in same category
    related = []
    for cmd in get_commands_by_category(cmd_data["category"]):
        if cmd["full_name"] != cmd_data["full_name"]:
            related.append(cmd["full_name"])

    if related:
        help_text.append("SEE ALSO\n", style="bold")
        help_text.append(f"    {', '.join(related[:5])}\n")

    console.print(Panel(help_text, title=f"cli.py {cmd_data['full_name']}", border_style="green"))


@app.command()
def categories():
    """List all command categories."""
    output_json(
        {
            "categories": [
                {"name": name, "description": data["description"], "command_count": len(data["commands"])}
                for name, data in COMMAND_REGISTRY.items()
            ],
            "total_categories": len(COMMAND_REGISTRY),
        }
    )
