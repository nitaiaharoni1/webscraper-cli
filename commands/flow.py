"""Conditional flow control commands."""

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


@app.command(name='if')
def if_command(
    selector: str,
    then_command: str = typer.Option(..., help='Command to run if element exists'),
    else_command: Optional[str] = typer.Option(None, help='Command to run if element does not exist'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Execute command conditionally based on element presence."""
    import asyncio
    import subprocess

    async def _if():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')
        
        # Check if element exists
        locator = connection.page.locator(selector).first
        exists = await locator.count() > 0
        
        if exists:
            output_result({
                'condition': 'true',
                'selector': selector,
                'executing': then_command
            })
            
            # Execute then command
            result = subprocess.run(then_command, shell=True, capture_output=True, text=True)
            output_result({
                'command': then_command,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None
            })
        else:
            output_result({
                'condition': 'false',
                'selector': selector,
                'executing': else_command if else_command else 'nothing'
            })
            
            if else_command:
                # Execute else command
                result = subprocess.run(else_command, shell=True, capture_output=True, text=True)
                output_result({
                    'command': else_command,
                    'output': result.stdout,
                    'error': result.stderr if result.returncode != 0 else None
                })

    asyncio.run(_if())


@app.command()
def exists(
    selector: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Check if element exists (returns boolean)."""
    import asyncio

    async def _exists():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')
        
        locator = connection.page.locator(selector).first
        exists = await locator.count() > 0
        
        output_result({
            'selector': selector,
            'exists': exists,
            'url': connection.page.url
        })

    asyncio.run(_exists())


@app.command()
def loop(
    selector: str,
    command: str = typer.Option(..., help='Command to run for each element'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    max_iterations: int = typer.Option(100, help='Maximum iterations'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Loop through elements and execute command for each."""
    import asyncio
    import subprocess

    async def _loop():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')
        
        locator = connection.page.locator(selector)
        count = await locator.count()
        
        iterations = min(count, max_iterations)
        results = []
        
        for i in range(iterations):
            element = locator.nth(i)
            
            # Get element text or identifier
            text = await element.text_content()
            
            output_result({
                'iteration': i + 1,
                'element': text[:50] if text else f'Element {i}',
                'executing': command
            })
            
            # Execute command (can use $INDEX placeholder)
            cmd = command.replace('$INDEX', str(i))
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            results.append({
                'iteration': i + 1,
                'command': cmd,
                'output': result.stdout,
                'success': result.returncode == 0
            })
        
        output_result({
            'total_iterations': iterations,
            'results': results
        })

    asyncio.run(_loop())
