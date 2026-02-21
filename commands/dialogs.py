"""Dialog handling commands (alert, confirm, prompt)."""

from typing import Optional

import typer

from core.async_command import get_connection, run_async
from core.output import output_json

app = typer.Typer()


@app.command()
def accept(
    text: Optional[str] = typer.Option(None, help="Text to enter (for prompt dialogs)"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Accept a dialog (alert/confirm) or enter text (prompt)."""

    async def _accept():
        connection = await get_connection(session_id, headless, url)

        # Set up dialog handler
        dialog_handled = {"accepted": False}

        def handle_dialog(dialog):
            dialog_handled["accepted"] = True
            if text:
                dialog.accept(text)
            else:
                dialog.accept()

        connection.page.on("dialog", handle_dialog)

        # Wait a bit for dialog to appear (or trigger action that shows dialog)
        await connection.page.wait_for_timeout(1000)

        output_json({"message": "Dialog handler set up. Dialog will be accepted when it appears."})

    run_async(_accept())


@app.command()
def dismiss(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Dismiss a dialog."""

    async def _dismiss():
        connection = await get_connection(session_id, headless, url)

        def handle_dialog(dialog):
            dialog.dismiss()

        connection.page.on("dialog", handle_dialog)
        await connection.page.wait_for_timeout(1000)

        output_json({"message": "Dialog handler set up. Dialog will be dismissed when it appears."})

    run_async(_dismiss())
