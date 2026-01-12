"""Assertion commands for validation."""

import typer
import json
import sys
from typing import Optional
from core.browser import get_or_create_connection, get_browser_manager
from core import settings
from core.errors import CLIError

app = typer.Typer()


def output_json(data: dict):
    """Output JSON data."""
    if not settings.quiet:
        print(json.dumps(data, indent=2))


@app.command()
def exists(
    selector: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Assert that an element exists."""
    import asyncio

    async def _assert_exists():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)

        count = await connection.page.locator(selector).count()
        if count == 0:
            raise CLIError(f'Element "{selector}" does not exist', f'Check if the selector is correct: {selector}')
            
        output_json({'message': f'Element "{selector}" exists', 'count': count})

    try:
        asyncio.run(_assert_exists())
    except CLIError as e:
        from core.progress import log_error
        log_error(str(e))
        sys.exit(1)


@app.command()
def text(
    selector: str,
    contains: Optional[str] = typer.Option(None, help='Assert text contains this string'),
    equals: Optional[str] = typer.Option(None, help='Assert text equals this string'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Assert text content of an element."""
    import asyncio

    async def _assert_text():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        element = connection.page.locator(selector).first
        text_content = await element.text_content()
        actual_text = text_content.strip() if text_content else ''

        if contains:
            if contains not in actual_text:
                raise CLIError(
                    f'Text "{actual_text}" does not contain "{contains}"',
                    f'Expected text containing "{contains}" but got "{actual_text}"'
                )
            output_json({'message': f'Text contains "{contains}"', 'actual': actual_text})
        elif equals:
            if actual_text != equals:
                raise CLIError(
                    f'Text "{actual_text}" does not equal "{equals}"',
                    f'Expected "{equals}" but got "{actual_text}"'
                )
            output_json({'message': f'Text equals "{equals}"', 'actual': actual_text})
        else:
            raise CLIError('Must specify either --contains or --equals')

    try:
        asyncio.run(_assert_text())
    except CLIError as e:
        from core.progress import log_error
        log_error(str(e))
        sys.exit(1)


@app.command()
def count(
    selector: str,
    equals: Optional[int] = typer.Option(None, help='Assert count equals this number'),
    min: Optional[int] = typer.Option(None, help='Assert count is at least this number'),
    max: Optional[int] = typer.Option(None, help='Assert count is at most this number'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Assert count of elements matching selector."""
    import asyncio

    async def _assert_count():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        actual_count = await connection.page.locator(selector).count()

        if equals is not None:
            if actual_count != equals:
                raise CLIError(
                    f'Count {actual_count} does not equal {equals}',
                    f'Expected {equals} elements but found {actual_count}'
                )
            output_json({'message': f'Count equals {equals}', 'actual': actual_count})
        elif min is not None:
            if actual_count < min:
                raise CLIError(
                    f'Count {actual_count} is less than {min}',
                    f'Expected at least {min} elements but found {actual_count}'
                )
            output_json({'message': f'Count >= {min}', 'actual': actual_count})
        elif max is not None:
            if actual_count > max:
                raise CLIError(
                    f'Count {actual_count} is greater than {max}',
                    f'Expected at most {max} elements but found {actual_count}'
                )
            output_json({'message': f'Count <= {max}', 'actual': actual_count})
        else:
            raise CLIError('Must specify --equals, --min, or --max')

    try:
        asyncio.run(_assert_count())
    except CLIError as e:
        from core.progress import log_error
        log_error(str(e))
        sys.exit(1)


@app.command()
def visible(
    selector: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Assert that an element is visible."""
    import asyncio

    async def _assert_visible():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        element = connection.page.locator(selector).first
        is_visible = await element.is_visible()
            
        if not is_visible:
            raise CLIError(
                f'Element "{selector}" is not visible',
                f'Check if the element exists and is not hidden by CSS'
            )
            
        output_json({'message': f'Element "{selector}" is visible'})

    try:
        asyncio.run(_assert_visible())
    except CLIError as e:
        from core.progress import log_error
        log_error(str(e))
        sys.exit(1)
