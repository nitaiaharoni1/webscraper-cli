"""Network interception and request monitoring commands."""

import typer
import json
from typing import Optional, List
from core.browser import get_or_create_connection, get_browser_manager
from core import settings

app = typer.Typer()


def output_json(data: dict):
    """Output JSON data."""
    if not settings.quiet:
        print(json.dumps(data, indent=2))


@app.command()
def intercept(
    block: Optional[str] = typer.Option(None, help='URL pattern to block (glob)'),
    modify: Optional[str] = typer.Option(None, help='JSON file with request modifications'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Intercept, block, or modify network requests."""
    import asyncio
    import fnmatch

    async def _intercept():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)

            async def handle_route(route):
                request_url = route.request.url
                
                if block and fnmatch.fnmatch(request_url, block):
                    await route.abort()
                    return
                
                if modify:
                    # Load modifications from file
                    with open(modify, 'r') as f:
                        mods = json.load(f)
                    
                    # Modify request if needed
                    if 'headers' in mods:
                        headers = route.request.headers.copy()
                        headers.update(mods['headers'])
                        await route.continue_(headers=headers)
                    else:
                        await route.continue_()
                else:
                    await route.continue_()

            await connection.page.route('**/*', handle_route)
            output_json({'message': 'Network interception enabled'})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_intercept())


@app.command()
def requests(
    filter_pattern: Optional[str] = typer.Option(None, help='Filter requests by URL pattern'),
    format: str = typer.Option('json', help='Output format: json, table'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """List all network requests."""
    import asyncio

    async def _requests():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        requests_list = []

        def handle_request(request):
            requests_list.append({
                'url': request.url,
                'method': request.method,
                'headers': dict(request.headers),
            })

        connection.page.on('request', handle_request)

        try:
            if url:
                await connection.page.goto(url, wait_until='networkidle', timeout=settings.timeout)
            else:
                await connection.page.wait_for_timeout(2000)

            if filter_pattern:
                import fnmatch
                requests_list = [r for r in requests_list if fnmatch.fnmatch(r['url'], filter_pattern)]

            if format == 'table':
                from rich.console import Console
                from rich.table import Table
                console = Console()
                table = Table(show_header=True, header_style='bold magenta')
                table.add_column('Method')
                table.add_column('URL')
                for req in requests_list[:50]:  # Limit to 50
                    table.add_row(req['method'], req['url'][:80])
                if not settings.quiet:
                    console.print(table)
            else:
                output_json({'requests': requests_list, 'count': len(requests_list)})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_requests())


@app.command()
def headers(
    action: str = typer.Argument(..., help='Action: set, get, clear'),
    name: Optional[str] = typer.Option(None, help='Header name'),
    value: Optional[str] = typer.Option(None, help='Header value'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Set custom request headers."""
    import asyncio

    async def _headers():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if action == 'set' and name and value:
                await connection.context.set_extra_http_headers({name: value})
                output_json({'message': f'Set header {name}: {value}'})
            elif action == 'get':
                headers = connection.context.extra_http_headers or {}
                output_json({'headers': headers})
            elif action == 'clear':
                await connection.context.set_extra_http_headers({})
                output_json({'message': 'Cleared custom headers'})
            else:
                output_json({'error': 'Invalid action or missing parameters'})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_headers())


@app.command()
def auth(
    username: str = typer.Option(..., help='Username'),
    password: str = typer.Option(..., help='Password'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Set HTTP Basic Authentication credentials."""
    import asyncio
    import base64

    async def _auth():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            credentials = base64.b64encode(f'{username}:{password}'.encode()).decode()
            await connection.context.set_extra_http_headers({
                'Authorization': f'Basic {credentials}'
            })
            
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)
            
            output_json({'message': 'HTTP Basic Auth configured'})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_auth())


@app.command()
def throttle(
    preset: str = typer.Option('slow-3g', help='Network preset: slow-3g, fast-3g, slow-4g, fast-4g, offline'),
    download: Optional[int] = typer.Option(None, help='Download speed (bytes/sec)'),
    upload: Optional[int] = typer.Option(None, help='Upload speed (bytes/sec)'),
    latency: Optional[int] = typer.Option(None, help='Latency (ms)'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Simulate slow network conditions."""
    import asyncio

    async def _throttle():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        
        # Network presets (bytes per second)
        presets = {
            'slow-3g': {'download': 50 * 1024, 'upload': 50 * 1024, 'latency': 2000},
            'fast-3g': {'download': 100 * 1024, 'upload': 75 * 1024, 'latency': 562},
            'slow-4g': {'download': 500 * 1024, 'upload': 500 * 1024, 'latency': 400},
            'fast-4g': {'download': 4 * 1024 * 1024, 'upload': 3 * 1024 * 1024, 'latency': 170},
            'offline': {'download': 0, 'upload': 0, 'latency': 0}
        }
        
        if preset in presets:
            config = presets[preset]
        else:
            config = {
                'download': download or -1,
                'upload': upload or -1,
                'latency': latency or 0
            }
        
        try:
            # Use CDP to set network conditions
            cdp = await connection.context.new_cdp_session(connection.page)
            await cdp.send('Network.emulateNetworkConditions', {
                'offline': preset == 'offline',
                'downloadThroughput': config['download'],
                'uploadThroughput': config['upload'],
                'latency': config['latency']
            })
            
            output_json({
                'message': f'Network throttling enabled: {preset}',
                'config': config
            })
            
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout * 2)
                output_json({'message': f'Navigated to {url} with throttling'})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_throttle())


@app.command()
def offline(
    enable: bool = typer.Option(True, help='Enable or disable offline mode'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Toggle offline mode."""
    import asyncio

    async def _offline():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        
        try:
            await connection.context.set_offline(enable)
            output_json({
                'message': f'Offline mode {"enabled" if enable else "disabled"}'
            })
            
            if url:
                try:
                    await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)
                    output_json({'message': f'Navigated to {url}'})
                except Exception as e:
                    output_json({'error': f'Navigation failed (offline mode): {str(e)}'})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_offline())


@app.command()
def websocket(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    duration: int = typer.Option(10, help='Duration to monitor (seconds)'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Monitor WebSocket connections and messages."""
    import asyncio

    async def _websocket():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        
        websockets = []
        messages = []
        
        def on_websocket(ws):
            ws_info = {'url': ws.url, 'messages': []}
            websockets.append(ws_info)
            
            ws.on('framereceived', lambda payload: messages.append({
                'type': 'received',
                'url': ws.url,
                'payload': payload.get('payload', '')[:200]  # Limit size
            }))
            
            ws.on('framesent', lambda payload: messages.append({
                'type': 'sent',
                'url': ws.url,
                'payload': payload.get('payload', '')[:200]
            }))
            
            ws.on('close', lambda: ws_info.update({'closed': True}))
        
        connection.page.on('websocket', on_websocket)
        
        try:
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)
            
            # Monitor for specified duration
            await asyncio.sleep(duration)
            
            output_json({
                'websockets': websockets,
                'messages': messages,
                'summary': {
                    'totalWebSockets': len(websockets),
                    'totalMessages': len(messages)
                }
            })
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_websocket())
