"""Shadow DOM access commands."""

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
def access(
    host_selector: str = typer.Argument(..., help='CSS selector of shadow host element'),
    inner_selector: str = typer.Option(..., '--selector', '-s', help='CSS selector inside shadow DOM'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Access elements inside Shadow DOM."""
    import asyncio

    async def _shadow_dom():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)

            # Access shadow DOM via JavaScript
            result = await connection.page.evaluate(f'''
                () => {{
                    const hostSelector = {json.dumps(host_selector)};
                    const innerSelector = {json.dumps(inner_selector)};
                    const host = document.querySelector(hostSelector);
                    if (!host || !host.shadowRoot) {{
                        return {{error: 'Shadow root not found'}};
                    }}
                    const elements = host.shadowRoot.querySelectorAll(innerSelector);
                    return Array.from(elements).map(el => ({{
                        text: el.textContent?.trim() || '',
                        html: el.outerHTML,
                        tag: el.tagName.toLowerCase()
                    }}));
                }}
            ''')

            if isinstance(result, dict) and 'error' in result:
                output_json(result)
            elif len(result) == 1:
                output_json({'result': result[0]})
            else:
                output_json({'results': result})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_shadow_dom())
