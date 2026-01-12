"""Storage commands (cookies, localStorage, sessionStorage)."""

import typer
import json
from typing import Optional
from core.browser import get_or_create_connection, get_browser_manager

app = typer.Typer()


def output_json(data):
    """Output JSON data."""
    print(json.dumps(data, indent=2))


# Cookies subcommands
cookies_app = typer.Typer()
app.add_typer(cookies_app, name='cookies')


@cookies_app.command()
def get(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    name: Optional[str] = typer.Option(None, help='Get specific cookie by name'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Get cookies."""
    import asyncio

    async def _get_cookies():
        connection = await get_or_create_connection(session_id, headless=headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        cookies = await connection.context.cookies()
        if name:
            cookies = [c for c in cookies if c['name'] == name]

        output_json(cookies)

    asyncio.run(_get_cookies())


@cookies_app.command()
def set(
    name: str,
    value: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    domain: Optional[str] = typer.Option(None, help='Cookie domain'),
    path: Optional[str] = typer.Option(None, help='Cookie path'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Set a cookie."""
    import asyncio

    async def _set_cookie():
        connection = await get_or_create_connection(session_id, headless=headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        cookie_data = {
            'name': name,
            'value': value,
            'domain': domain or connection.page.url.split('/')[2] if connection.page.url else '',
            'path': path or '/',
        }
        await connection.context.add_cookies([cookie_data])
        output_json({'message': f'Cookie {name} set'})

    asyncio.run(_set_cookie())


@cookies_app.command()
def clear(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Clear all cookies."""
    import asyncio

    async def _clear_cookies():
        connection = await get_or_create_connection(session_id, headless=headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        await connection.context.clear_cookies()
        output_json({'message': 'All cookies cleared'})

    asyncio.run(_clear_cookies())


# LocalStorage subcommands
localstorage_app = typer.Typer()
app.add_typer(localstorage_app, name='localstorage')


@localstorage_app.command()
def get(
    key: Optional[str] = typer.Option(None, help='Get specific key, or all if not specified'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Get localStorage value(s)."""
    import asyncio

    async def _get_localstorage():
        connection = await get_or_create_connection(session_id, headless=headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        if key:
            value = await connection.page.evaluate(f'localStorage.getItem("{key}")')
            output_json({key: value})
        else:
            items = await connection.page.evaluate('''() => {
                const result = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    result[key] = localStorage.getItem(key);
                }
                return result;
            }''')
            output_json(items)

    asyncio.run(_get_localstorage())


@localstorage_app.command()
def set(
    key: str,
    value: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Set localStorage value."""
    import asyncio

    async def _set_localstorage():
        connection = await get_or_create_connection(session_id, headless=headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        await connection.page.evaluate(f'localStorage.setItem("{key}", "{value}")')
        output_json({'message': f'localStorage[{key}] = {value}'})

    asyncio.run(_set_localstorage())


@localstorage_app.command()
def clear(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Clear all localStorage."""
    import asyncio

    async def _clear_localstorage():
        connection = await get_or_create_connection(session_id, headless=headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        await connection.page.evaluate('localStorage.clear()')
        output_json({'message': 'localStorage cleared'})

    asyncio.run(_clear_localstorage())
