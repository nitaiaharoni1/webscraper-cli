"""Clipboard and text selection commands."""

import typer
import json
from typing import Optional
from core.browser import get_or_create_connection, get_browser_manager
from core import settings

app = typer.Typer()


def output_json(data: dict):
    """Output JSON data."""
    if not settings.quiet:
        print(json.dumps(data, indent=2))


@app.command()
def copy(
    selector: Optional[str] = typer.Option(None, help='CSS selector to copy (default: selected text)'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Copy text or element to system clipboard."""
    import asyncio
    import pyperclip

    async def _copy():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)

            if selector:
                text = await connection.page.locator(selector).first.text_content()
            else:
                # Get selected text
                text = await connection.page.evaluate('window.getSelection().toString()')

            if text:
                pyperclip.copy(text.strip())
                output_json({'message': f'Copied to clipboard: {text[:50]}...' if len(text) > 50 else f'Copied to clipboard: {text}'})
            else:
                output_json({'error': 'No text to copy'})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_copy())


@app.command()
def paste(
    selector: str = typer.Argument(..., help='CSS selector of input/textarea'),
    text: Optional[str] = typer.Option(None, help='Text to paste (default: from clipboard)'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Paste text from clipboard into input field."""
    import asyncio
    import pyperclip

    async def _paste():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)

            if not text:
                text = pyperclip.paste()

            locator = connection.page.locator(selector).first
            await locator.fill(text)
            output_json({'message': f'Pasted text into {selector}'})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_paste())


@app.command()
def select_text(
    selector: str = typer.Argument(..., help='CSS selector'),
    start: int = typer.Option(0, help='Start position'),
    end: Optional[int] = typer.Option(None, help='End position (default: end of text)'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Select text range in element."""
    import asyncio

    async def _select_text():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)

            await connection.page.evaluate(f'''
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
            ''')

            output_json({'message': f'Selected text in {selector}'})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_select_text())
