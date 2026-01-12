"""Local server commands."""

import typer
import json
from typing import Optional
from pathlib import Path

app = typer.Typer()


def output_result(data):
    """Output data in the configured format."""
    print(json.dumps(data, indent=2))


@app.command()
def start(
    directory: str = typer.Option('.', help='Directory to serve'),
    port: int = typer.Option(8000, help='Port to listen on'),
    host: str = typer.Option('localhost', help='Host to bind to'),
):
    """Start a local HTTP server for testing."""
    import asyncio
    from aiohttp import web

    async def handle_request(request):
        """Handle HTTP requests."""
        path = request.path
        if path == '/':
            path = '/index.html'
        
        file_path = Path(directory) / path.lstrip('/')
        
        if not file_path.exists():
            return web.Response(text='404 Not Found', status=404)
        
        if file_path.is_dir():
            # List directory
            files = list(file_path.iterdir())
            html = '<html><body><h1>Directory listing</h1><ul>'
            for f in files:
                html += f'<li><a href="{f.name}">{f.name}</a></li>'
            html += '</ul></body></html>'
            return web.Response(text=html, content_type='text/html')
        
        # Serve file
        content_type = 'text/plain'
        if file_path.suffix == '.html':
            content_type = 'text/html'
        elif file_path.suffix == '.css':
            content_type = 'text/css'
        elif file_path.suffix == '.js':
            content_type = 'application/javascript'
        elif file_path.suffix == '.json':
            content_type = 'application/json'
        elif file_path.suffix in ['.jpg', '.jpeg']:
            content_type = 'image/jpeg'
        elif file_path.suffix == '.png':
            content_type = 'image/png'
        elif file_path.suffix == '.gif':
            content_type = 'image/gif'
        
        with open(file_path, 'rb') as f:
            return web.Response(body=f.read(), content_type=content_type)

    async def start_server():
        app_web = web.Application()
        app_web.router.add_route('*', '/{path:.*}', handle_request)
        
        runner = web.AppRunner(app_web)
        await runner.setup()
        
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        output_result({
            'message': f'Server started',
            'url': f'http://{host}:{port}',
            'directory': directory
        })
        
        # Keep server running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            output_result({'message': 'Server stopped'})

    asyncio.run(start_server())


@app.command()
def proxy(
    target: str = typer.Option(..., help='Target URL to proxy'),
    port: int = typer.Option(8080, help='Port to listen on'),
    host: str = typer.Option('localhost', help='Host to bind to'),
):
    """Start a proxy server."""
    import asyncio
    from aiohttp import web, ClientSession

    async def handle_proxy(request):
        """Proxy requests to target."""
        async with ClientSession() as session:
            url = f'{target}{request.path}'
            
            async with session.request(
                method=request.method,
                url=url,
                headers=request.headers,
                data=await request.read()
            ) as response:
                return web.Response(
                    body=await response.read(),
                    status=response.status,
                    headers=response.headers
                )

    async def start_proxy():
        app_web = web.Application()
        app_web.router.add_route('*', '/{path:.*}', handle_proxy)
        
        runner = web.AppRunner(app_web)
        await runner.setup()
        
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        output_result({
            'message': 'Proxy server started',
            'proxy_url': f'http://{host}:{port}',
            'target': target
        })
        
        # Keep server running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            output_result({'message': 'Proxy stopped'})

    asyncio.run(start_proxy())
