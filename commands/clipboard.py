"""Clipboard and text selection commands."""

import json
from typing import Optional

import typer

from core.async_command import get_connection, run_async
from core.output import output_json

app = typer.Typer()


@app.command()
def copy(
    selector: Optional[str] = typer.Option(None, help="CSS selector to copy (default: selected text)"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Copy text or element to system clipboard."""
    import pyperclip

    async def _copy():
        connection = await get_connection(session_id, headless, url)
        try:
            if selector:
                text = await connection.page.locator(selector).first.text_content()
            else:
                # Get selected text
                text = await connection.page.evaluate("window.getSelection().toString()")

            if text:
                pyperclip.copy(text.strip())
                output_json(
                    {
                        "message": f"Copied to clipboard: {text[:50]}..."
                        if len(text) > 50
                        else f"Copied to clipboard: {text}"
                    }
                )
            else:
                output_json({"error": "No text to copy"})
        except Exception as e:
            output_json({"error": str(e)})

    run_async(_copy())


@app.command()
def paste(
    selector: str = typer.Argument(..., help="CSS selector of input/textarea"),
    text: Optional[str] = typer.Option(None, help="Text to paste (default: from clipboard)"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Paste text from clipboard into input field."""
    import pyperclip

    async def _paste():
        connection = await get_connection(session_id, headless, url)
        try:
            paste_text = text
            if not paste_text:
                paste_text = pyperclip.paste()

            locator = connection.page.locator(selector).first
            await locator.fill(paste_text)
            output_json({"message": f"Pasted text into {selector}"})
        except Exception as e:
            output_json({"error": str(e)})

    run_async(_paste())


@app.command()
def select_text(
    selector: str = typer.Argument(..., help="CSS selector"),
    start: int = typer.Option(0, help="Start position"),
    end: Optional[int] = typer.Option(None, help="End position (default: end of text)"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Select text range in element."""

    async def _select_text():
        connection = await get_connection(session_id, headless, url)
        try:
            await connection.page.evaluate(f"""
                () => {{
                    const selector = {json.dumps(selector)};
                    const start = {start};
                    const end = {json.dumps(end)};
                    const el = document.querySelector(selector);
                    if (el) {{
                        const range = document.createRange();
                        const textNode = el.firstChild;
                        if (textNode) {{
                            const textLength = textNode.textContent.length;
                            range.setStart(textNode, Math.min(start, textLength));
                            range.setEnd(textNode, end !== null ? Math.min(end, textLength) : textLength);
                            const selection = window.getSelection();
                            selection.removeAllRanges();
                            selection.addRange(range);
                        }}
                    }}
                }}
            """)

            output_json({"message": f"Selected text in {selector}"})
        except Exception as e:
            output_json({"error": str(e)})

    run_async(_select_text())
