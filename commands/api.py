"""Browser API execution commands."""

import typer
import json
from typing import Optional
from core.browser import get_or_create_connection
from core.settings import settings

app = typer.Typer()


def output_result(data):
    """Output data in the configured format."""
    if settings.format == 'json':
        print(json.dumps(data, indent=2))
    else:
        print(data)


@app.command()
def fetch(
    url: str,
    method: str = typer.Option('GET', help='HTTP method'),
    headers: Optional[str] = typer.Option(None, help='JSON string of headers'),
    body: Optional[str] = typer.Option(None, help='Request body'),
    navigate_to: Optional[str] = typer.Option(None, '--navigate-to', '-n', help='Navigate to this URL first to establish browser context'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Execute fetch request from browser context (inherits cookies, auth, CORS).
    
    Inherits cookies, authentication headers, and CORS context from the current page.
    Useful for making API calls that require authentication.
    
    Examples:
        cli.py api fetch "https://api.example.com/data"
        cli.py api fetch "https://api.example.com/post" --method POST --body '{"key": "value"}'
        cli.py api fetch "https://api.example.com/users" --headers '{"Authorization": "Bearer token"}'
        cli.py api fetch "https://api.example.com/data" --navigate-to "https://example.com/login"
    """
    import asyncio

    async def _fetch():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        # Navigate to a page first if specified (to establish context)
        if navigate_to:
            await connection.page.goto(navigate_to, wait_until='domcontentloaded')
        
        # Build fetch options
        fetch_options = {'method': method}
        if headers:
            fetch_options['headers'] = json.loads(headers)
        if body:
            fetch_options['body'] = body

        # Execute fetch in browser context
        result = await connection.page.evaluate(f'''
            async () => {{
                try {{
                    const response = await fetch({json.dumps(url)}, {json.dumps(fetch_options)});
                    const text = await response.text();
                    let data;
                    try {{
                        data = JSON.parse(text);
                    }} catch (e) {{
                        data = text;
                    }}
                    return {{
                        ok: response.ok,
                        status: response.status,
                        statusText: response.statusText,
                        headers: Object.fromEntries(response.headers.entries()),
                        data: data
                    }};
                }} catch (error) {{
                    return {{
                        error: error.message
                    }};
                }}
            }}
        ''')

        output_result(result)

    asyncio.run(_fetch())


@app.command()
def har(
    output_file: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Export HTTP Archive (HAR) of network activity."""
    import asyncio

    async def _har():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        # Start recording network activity
        requests_log = []
        
        async def log_request(request):
            requests_log.append({
                'url': request.url,
                'method': request.method,
                'headers': request.headers,
                'postData': request.post_data,
                'timestamp': request.timing['requestStart'] if request.timing else None
            })
        
        async def log_response(response):
            for req in requests_log:
                if req['url'] == response.url:
                    req['response'] = {
                        'status': response.status,
                        'statusText': response.status_text,
                        'headers': response.headers,
                    }
                    break
        
        connection.page.on('request', log_request)
        connection.page.on('response', log_response)
        
        if url:
            await connection.page.goto(url, wait_until='networkidle')
        
        # Save HAR
        har_data = {
            'log': {
                'version': '1.2',
                'creator': {'name': 'agent-service', 'version': '1.0'},
                'entries': requests_log
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(har_data, f, indent=2)
        
        output_result({
            'message': f'HAR saved to {output_file}',
            'requests': len(requests_log)
        })

    asyncio.run(_har())


@app.command()
def mock(
    pattern: str,
    response_file: Optional[str] = typer.Option(None, help='JSON file with mock response'),
    response_json: Optional[str] = typer.Option(None, help='JSON string for mock response'),
    status: int = typer.Option(200, help='HTTP status code'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Mock API endpoints with custom responses."""
    import asyncio

    async def _mock():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        # Load mock response
        if response_file:
            with open(response_file, 'r') as f:
                mock_data = json.load(f)
        elif response_json:
            mock_data = json.loads(response_json)
        else:
            mock_data = {'mocked': True}
        
        # Set up route handler
        async def handle_route(route):
            await route.fulfill(
                status=status,
                body=json.dumps(mock_data),
                headers={'Content-Type': 'application/json'}
            )
        
        await connection.page.route(pattern, handle_route)
        
        output_result({
            'message': f'Mocking requests matching: {pattern}',
            'status': status
        })
        
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')
            output_result({'message': f'Navigated to {url} with mocked endpoint'})

    asyncio.run(_mock())
