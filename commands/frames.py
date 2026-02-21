"""Frame/iframe handling commands."""

from typing import Optional

import typer

from core.async_command import get_connection, run_async
from core.output import output_json

app = typer.Typer()

# Store current frame context per session
_frame_contexts: dict[str, str] = {}


@app.command()
def switch(
    selector: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Switch to an iframe."""

    async def _switch():
        connection = await get_connection(session_id, headless, url)
        effective_session_id = session_id or "default"

        frame_locator = connection.page.frame_locator(selector)
        _frame_contexts[effective_session_id] = selector

        # Verify frame exists
        frame_locator.first
        output_json({"message": f"Switched to frame {selector}"})

    run_async(_switch())


@app.command()
def main(
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Switch back to main frame."""

    async def _main():
        await get_connection(session_id, headless)
        effective_session_id = session_id or "default"

        _frame_contexts[effective_session_id] = "main"
        output_json({"message": "Switched to main frame"})

    run_async(_main())


@app.command()
def list_frames(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """List all frames on the page."""

    async def _list():
        connection = await get_connection(session_id, headless, url)

        frames = await connection.page.evaluate("""
            Array.from(document.querySelectorAll('iframe'))
                .map((iframe, index) => ({
                    index: index,
                    src: iframe.src || '',
                    id: iframe.id || '',
                    name: iframe.name || '',
                    selector: iframe.id ? `#${iframe.id}` : iframe.name ? `[name="${iframe.name}"]` : `iframe:nth-of-type(${index + 1})`
                }))
        """)

        output_json({"frames": frames})

    run_async(_list())
