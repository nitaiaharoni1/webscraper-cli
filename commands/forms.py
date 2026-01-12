"""Form automation commands."""

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
def fill(
    selector: str = typer.Argument(..., help='CSS selector of form'),
    data: str = typer.Option(..., '--data', '-d', help='JSON string or path to JSON/YAML file with form data'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Auto-fill form from JSON string or JSON/YAML file."""
    import asyncio
    import yaml

    async def _fill():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)

            # Load form data - support both inline JSON and file paths
            form_data = None
            
            # Try parsing as JSON string first
            try:
                form_data = json.loads(data)
            except json.JSONDecodeError:
                pass
            
            # If not valid JSON, try as file path
            if form_data is None and os.path.exists(data):
                with open(data, 'r') as f:
                    if data.endswith('.yaml') or data.endswith('.yml'):
                        form_data = yaml.safe_load(f)
                    else:
                        form_data = json.load(f)
            
            if form_data is None:
                output_json({'error': f'Invalid data: not valid JSON and file not found: {data}'})
                return

            form_locator = connection.page.locator(selector).first
            
            # Fill form fields
            filled = []
            for field_name, value in form_data.items():
                # Try multiple selectors
                selectors = [
                    f'input[name="{field_name}"]',
                    f'input[id="{field_name}"]',
                    f'textarea[name="{field_name}"]',
                    f'select[name="{field_name}"]',
                ]
                
                filled_field = False
                for sel in selectors:
                    try:
                        field = form_locator.locator(sel).first
                        if await field.count() > 0:
                            tag_name = await field.evaluate('el => el.tagName.toLowerCase()')
                            if tag_name == 'select':
                                await field.select_option(str(value))
                            else:
                                await field.fill(str(value))
                            filled.append(field_name)
                            filled_field = True
                            break
                    except Exception:
                        continue
                
                if not filled_field:
                    output_json({'warning': f'Field {field_name} not found'})

            output_json({'message': f'Filled {len(filled)} fields', 'fields': filled})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_fill())


@app.command()
def submit(
    selector: str = typer.Argument(..., help='CSS selector of form'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Submit a form."""
    import asyncio

    async def _submit():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)

            form_locator = connection.page.locator(selector).first
            await form_locator.evaluate('form => form.submit()')
            
            # Wait for navigation
            await connection.page.wait_for_load_state('networkidle', timeout=settings.timeout)
            
            output_json({
                'message': 'Form submitted',
                'url': connection.page.url,
                'title': await connection.page.title()
            })
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_submit())
