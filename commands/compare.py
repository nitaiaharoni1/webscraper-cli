"""Page comparison and snapshot commands."""

import typer
import json
import os
from typing import Optional
from core.browser import get_or_create_connection, get_browser_manager
from core import settings

app = typer.Typer()


def output_json(data: dict):
    """Output JSON data."""
    if not settings.quiet:
        print(json.dumps(data, indent=2))


@app.command()
def snapshot(
    output: str = typer.Option('snapshot.json', '--output', '-o', help='Output file path'),
    selector: Optional[str] = typer.Option(None, help='CSS selector (default: body)'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Save page snapshot for comparison."""
    import asyncio

    async def _snapshot():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)

            if selector:
                html = await connection.page.locator(selector).first.inner_html()
                text = await connection.page.locator(selector).first.text_content()
            else:
                html = await connection.page.content()
                text = await connection.page.evaluate('document.body.textContent')

            timestamp = await connection.page.evaluate('Date.now()')
            snapshot_data = {
                'url': connection.page.url,
                'title': await connection.page.title(),
                'html': html,
                'text': text.strip() if text else '',
                'timestamp': timestamp
            }

            with open(output, 'w', encoding='utf-8') as f:
                json.dump(snapshot_data, f, indent=2, ensure_ascii=False)

            output_json({'message': f'Snapshot saved to {output}'})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_snapshot())


@app.command()
def diff(
    snapshot1: str = typer.Option(..., '--snapshot1', '-s1', help='First snapshot file'),
    snapshot2: str = typer.Option(..., '--snapshot2', '-s2', help='Second snapshot file'),
    selector: Optional[str] = typer.Option(None, help='Compare specific selector'),
    format: str = typer.Option('json', help='Output format: json, unified'),
):
    """Compare two page snapshots."""
    import asyncio
    import difflib

    async def _diff():
        try:
            with open(snapshot1, 'r', encoding='utf-8') as f:
                snap1 = json.load(f)
            with open(snapshot2, 'r', encoding='utf-8') as f:
                snap2 = json.load(f)

            text1 = snap1.get('text', '')
            text2 = snap2.get('text', '')

            if format == 'unified':
                diff = difflib.unified_diff(
                    text1.splitlines(keepends=True),
                    text2.splitlines(keepends=True),
                    fromfile=snapshot1,
                    tofile=snapshot2,
                    lineterm=''
                )
                if not settings.quiet:
                    print(''.join(diff))
            else:
                diff_lines = list(difflib.unified_diff(
                    text1.splitlines(),
                    text2.splitlines(),
                    lineterm=''
                ))
                output_json({
                    'snapshot1': snapshot1,
                    'snapshot2': snapshot2,
                    'diff_lines': len(diff_lines),
                    'diff': diff_lines[:100]  # Limit to 100 lines
                })
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_diff())
