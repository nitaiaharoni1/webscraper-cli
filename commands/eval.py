"""JavaScript evaluation commands."""

from typing import Optional

import typer

from core.async_command import get_connection, run_async
from core.output import output_json, output_text

app = typer.Typer()


@app.command()
def run(
    code: str = typer.Argument("", help="JavaScript code to execute"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    file: Optional[str] = typer.Option(None, "--file", "-f", help="Read JavaScript code from file"),
    format: str = typer.Option("json", help="Output format: json, plain"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Run JavaScript code in page context and return result."""
    import os

    async def _eval():
        connection = await get_connection(session_id, headless, url)

        # Read code from file if provided
        if file:
            if not os.path.exists(file):
                output_json({"error": f"File not found: {file}"})
                return
            with open(file, "r") as f:
                js_code = f.read()
        else:
            js_code = code

        # Execute JavaScript
        result = await connection.page.evaluate(js_code)

        # Output result
        if format == "plain":
            output_text(str(result))
        else:
            output_json({"result": result})

    run_async(_eval())
