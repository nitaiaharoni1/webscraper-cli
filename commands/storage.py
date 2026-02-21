"""Storage commands (cookies, localStorage, sessionStorage)."""

from typing import Optional

import typer

from core.async_command import get_connection, run_async
from core.output import output_json

app = typer.Typer()


# Cookies subcommands
cookies_app = typer.Typer()
app.add_typer(cookies_app, name="cookies")


@cookies_app.command(name="get")
def cookies_get(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    name: Optional[str] = typer.Option(None, help="Get specific cookie by name"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Get cookies."""

    async def _get_cookies():
        connection = await get_connection(session_id, headless, url)

        cookies = await connection.context.cookies()
        if name:
            cookies = [c for c in cookies if c.get("name") == name]

        output_json(cookies)

    run_async(_get_cookies())


@cookies_app.command(name="set")
def cookies_set(
    name: str,
    value: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    domain: Optional[str] = typer.Option(None, help="Cookie domain"),
    path: Optional[str] = typer.Option(None, help="Cookie path"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Set a cookie."""

    async def _set_cookie():
        connection = await get_connection(session_id, headless, url)

        cookie_data = {
            "name": name,
            "value": value,
            "domain": domain or connection.page.url.split("/")[2] if connection.page.url else "",
            "path": path or "/",
        }
        await connection.context.add_cookies([cookie_data])
        output_json({"message": f"Cookie {name} set"})

    run_async(_set_cookie())


@cookies_app.command(name="clear")
def cookies_clear(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Clear all cookies."""

    async def _clear_cookies():
        connection = await get_connection(session_id, headless, url)

        await connection.context.clear_cookies()
        output_json({"message": "All cookies cleared"})

    run_async(_clear_cookies())


# LocalStorage subcommands
localstorage_app = typer.Typer()
app.add_typer(localstorage_app, name="localstorage")


@localstorage_app.command(name="get")
def localstorage_get(
    key: Optional[str] = typer.Option(None, help="Get specific key, or all if not specified"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Get localStorage value(s)."""

    async def _get_localstorage():
        connection = await get_connection(session_id, headless, url)

        if key:
            value = await connection.page.evaluate(f'localStorage.getItem("{key}")')
            output_json({key: value})
        else:
            items = await connection.page.evaluate("""() => {
                const result = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    result[key] = localStorage.getItem(key);
                }
                return result;
            }""")
            output_json(items)

    run_async(_get_localstorage())


@localstorage_app.command(name="set")
def localstorage_set(
    key: str,
    value: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Set localStorage value."""

    async def _set_localstorage():
        connection = await get_connection(session_id, headless, url)

        await connection.page.evaluate(f'localStorage.setItem("{key}", "{value}")')
        output_json({"message": f"localStorage[{key}] = {value}"})

    run_async(_set_localstorage())


@localstorage_app.command(name="clear")
def localstorage_clear(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Clear all localStorage."""

    async def _clear_localstorage():
        connection = await get_connection(session_id, headless, url)

        await connection.page.evaluate("localStorage.clear()")
        output_json({"message": "localStorage cleared"})

    run_async(_clear_localstorage())
