"""JavaScript evaluation commands."""

import typer
import json
from typing import Optional
from core.browser import get_or_create_connection, get_browser_manager

app = typer.Typer()


def output_json(data):
    """Output JSON data."""
    print(json.dumps(data, indent=2))


def output_text(text: str):
    """Output plain text."""
    print(text)


@app.command()
def run(
    code: str = typer.Argument('', help='JavaScript code to execute'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    file: Optional[str] = typer.Option(None, '--file', '-f', help='Read JavaScript code from file'),
    format: str = typer.Option('json', help='Output format: json, plain'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Run JavaScript code in page context and return result."""
    import asyncio
    import os

    async def _eval():
        connection = await get_or_create_connection(session_id, headless=headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        # Read code from file if provided
        if file:
            if not os.path.exists(file):
                output_json({'error': f'File not found: {file}'})
                return
            with open(file, 'r') as f:
                js_code = f.read()
        else:
            js_code = code

        # Execute JavaScript
        result = await connection.page.evaluate(js_code)

        # Output result
        if format == 'plain':
            output_text(str(result))
        else:
            output_json({'result': result})

    asyncio.run(_eval())
