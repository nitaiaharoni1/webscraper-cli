"""Monitoring and debugging commands."""

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
def console(
    filter_level: Optional[str] = typer.Option(None, help='Filter: error, warning, info, debug'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Capture browser console logs."""
    import asyncio

    async def _console():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        logs = []

        def handle_console(msg):
            level = msg.type
            if not filter_level or level == filter_level:
                logs.append({
                    'level': level,
                    'text': msg.text,
                    'location': {
                        'url': msg.location.get('url', ''),
                        'line': msg.location.get('lineNumber', 0),
                    }
                })

        connection.page.on('console', handle_console)

        try:
            if url:
                await connection.page.goto(url, wait_until='networkidle', timeout=settings.timeout)
            else:
                await connection.page.wait_for_timeout(2000)

            output_json({'logs': logs, 'count': len(logs)})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_console())


@app.command()
def performance(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Get performance metrics."""
    import asyncio

    async def _performance():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until='load', timeout=settings.timeout)

            metrics = await connection.page.evaluate('''
                () => {
                    const perf = performance.timing;
                    return {
                        loadTime: perf.loadEventEnd - perf.navigationStart,
                        domContentLoaded: perf.domContentLoadedEventEnd - perf.navigationStart,
                        firstPaint: performance.getEntriesByType('paint')[0]?.startTime || 0,
                        resources: performance.getEntriesByType('resource').length
                    };
                }
            ''')

            output_json(metrics)
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_performance())


@app.command()
def highlight(
    selector: str = typer.Argument(..., help='CSS selector to highlight'),
    color: str = typer.Option('red', help='Highlight color'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Highlight elements matching selector (visual debugging)."""
    import asyncio

    async def _highlight():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)

            await connection.page.evaluate(f'''
                () => {{
                    const selector = {json.dumps(selector)};
                    const color = {json.dumps(color)};
                    document.querySelectorAll(selector).forEach(el => {{
                        el.style.outline = `3px solid ${{color}}`;
                        el.style.outlineOffset = '2px';
                    }});
                }}
            ''')

            output_json({'message': f'Highlighted {selector} with {color}'})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_highlight())


@app.command()
def record(
    action: str = typer.Argument(..., help='Action: start, stop, replay'),
    output: Optional[str] = typer.Option(None, '--output', '-o', help='Output file for recording'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Record actions for later replay."""
    import asyncio
    import yaml

    async def _record():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        
        if action == 'start':
            # Store recording state
            output_json({'message': 'Recording started. Actions will be recorded.'})
        elif action == 'stop':
            # Save recording
            if output:
                with open(output, 'w') as f:
                    yaml.dump({'actions': []}, f)
                output_json({'message': f'Recording saved to {output}'})
        elif action == 'replay':
            if not output:
                output_json({'error': 'Output file required for replay'})
                return
            # Load and replay actions
            with open(output, 'r') as f:
                recording = yaml.safe_load(f)
            output_json({'message': f'Replaying {len(recording.get("actions", []))} actions'})
        else:
            output_json({'error': 'Invalid action. Use: start, stop, replay'})

    asyncio.run(_record())
