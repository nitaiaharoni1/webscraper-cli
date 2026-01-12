"""Extraction commands."""

import typer
import json
import csv
import sys
from typing import Optional, List, Dict, Any
from core.browser import get_or_create_connection, get_browser_manager
from core import settings

app = typer.Typer()


def output_json(data):
    """Output JSON data."""
    if not settings.quiet:
        print(json.dumps(data, indent=2))


def output_text(text: str):
    """Output plain text."""
    if not settings.quiet:
        print(text)


def output_csv(data: List[Dict[str, Any]]):
    """Output data as CSV."""
    if not data:
        return
    
    if not settings.quiet:
        writer = csv.DictWriter(sys.stdout, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)


def output_table(data: List[Dict[str, Any]]):
    """Output data as formatted table."""
    from rich.console import Console
    from rich.table import Table
    
    if not data:
        return
    
    console = Console()
    table = Table(show_header=True, header_style='bold magenta')
    
    # Add columns
    for key in data[0].keys():
        table.add_column(key)
    
    # Add rows
    for row in data:
        table.add_row(*[str(row.get(key, '')) for key in data[0].keys()])
    
    if not settings.quiet:
        console.print(table)


def format_output(data: Any, format_type: str):
    """Format output based on format type."""
    if format_type == 'csv':
        if isinstance(data, list) and data and isinstance(data[0], dict):
            output_csv(data)
        else:
            # Convert to list of dicts if needed
            if isinstance(data, dict):
                output_csv([data])
            else:
                output_json(data)
    elif format_type == 'table':
        if isinstance(data, list) and data and isinstance(data[0], dict):
            output_table(data)
        else:
            output_json(data)
    elif format_type == 'plain':
        if isinstance(data, list):
            output_text('\n'.join(str(item) for item in data))
        else:
            output_text(str(data))
    else:  # json
        output_json(data)


@app.command()
def text(
    selector: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    all: bool = typer.Option(False, '--all/--first', help='Extract from all matching elements'),
    format: Optional[str] = typer.Option(None, help='Output format: json, csv, plain, table (overrides global)'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode (overrides global)'),
):
    """Extract text from elements matching selector.
    
    Extracts text content from elements on the page. Can extract from a single
    element or all matching elements.
    
    Examples:
        cli.py extract text "h1" --url https://example.com
        cli.py extract text "p" --all --url https://example.com
        cli.py extract text ".title" --format plain
    """
    import asyncio

    async def _extract_text():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        # Optimize bulk extraction with single JS call
        if all:
            # Single JS call to extract all matching elements
            result = await connection.page.evaluate(f'''
                Array.from(document.querySelectorAll('{selector}'))
                    .map(el => el.textContent?.trim() || '')
                    .filter(text => text)
            ''')
        else:
            # Single JS call for first element
            result = await connection.page.evaluate(f'''
                (() => {{
                    const el = document.querySelector('{selector}');
                    return el ? el.textContent?.trim() || '' : '';
                }})()
            ''')

        format_output(result, format)

    asyncio.run(_extract_text())


@app.command()
def links(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    selector: Optional[str] = typer.Option('a', help='CSS selector for links'),
    absolute: bool = typer.Option(False, '--absolute/--relative', help='Convert relative URLs to absolute'),
    format: Optional[str] = typer.Option(None, help='Output format: json, csv, plain, table'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode (overrides global)'),
):
    """Extract links from page."""
    import asyncio

    async def _extract_links():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        # Optimize with single JS call
        base_url = connection.page.url
        links_data = await connection.page.evaluate(f'''
            Array.from(document.querySelectorAll('{selector}'))
                .map(el => ({{
                    href: el.getAttribute('href') || '',
                    text: el.textContent?.trim() || ''
                }}))
                .filter(link => link.href)
        ''')
            
        links = []
        for link_data in links_data:
            href = link_data['href']
            if absolute and not href.startswith(('http://', 'https://')):
                from urllib.parse import urljoin
                href = urljoin(base_url, href)
            links.append({
                'href': href,
                'text': link_data['text'],
            })

        format_output(links, format or settings.format)

    asyncio.run(_extract_links())


@app.command()
def html(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    selector: Optional[str] = typer.Option(None, help='CSS selector (extracts innerHTML if specified)'),
    outer: bool = typer.Option(False, '--outer/--inner', help='Extract outerHTML instead of innerHTML'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode (overrides global)'),
):
    """Extract HTML content."""
    import asyncio

    async def _extract_html():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        if selector:
            element = connection.page.locator(selector).first
            if outer:
                html_content = await element.evaluate('el => el.outerHTML')
            else:
                html_content = await element.evaluate('el => el.innerHTML')
        else:
            html_content = await connection.page.content()

        output_text(html_content)

    asyncio.run(_extract_html())


@app.command()
def attr(
    selector: str,
    attribute: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    all: bool = typer.Option(False, '--all/--first', help='Extract from all matching elements'),
    format: str = typer.Option('json', help='Output format: json, plain'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode (overrides global)'),
):
    """Extract attribute value from elements."""
    import asyncio

    async def _extract_attr():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        # Optimize with single JS call
        if all:
            result = await connection.page.evaluate(f'''
                Array.from(document.querySelectorAll('{selector}'))
                    .map(el => el.getAttribute('{attribute}'))
                    .filter(attr => attr)
            ''')
        else:
            result = await connection.page.evaluate(f'''
                (() => {{
                    const el = document.querySelector('{selector}');
                    return el ? el.getAttribute('{attribute}') || '' : '';
                }})()
            ''')

        format_output(result, format)

    asyncio.run(_extract_attr())


@app.command()
def count(
    selector: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode (overrides global)'),
):
    """Count elements matching selector."""
    import asyncio

    async def _count():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        locator = connection.page.locator(selector)
        count_value = await locator.count()
        output_json({'count': count_value, 'selector': selector})

    asyncio.run(_count())


@app.command()
def images(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    selector: Optional[str] = typer.Option('img', help='CSS selector for images'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode (overrides global)'),
):
    """Extract image URLs from page."""
    import asyncio

    async def _extract_images():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        # Optimize with single JS call
        base_url = connection.page.url
        images_data = await connection.page.evaluate(f'''
            Array.from(document.querySelectorAll('{selector}'))
                .map(el => ({{
                    src: el.getAttribute('src') || '',
                    alt: el.getAttribute('alt') || ''
                }}))
                .filter(img => img.src)
        ''')
            
        images = []
        for img_data in images_data:
            src = img_data['src']
            if not src.startswith(('http://', 'https://', 'data:')):
                from urllib.parse import urljoin
                src = urljoin(base_url, src)
            images.append({
                'src': src,
                'alt': img_data['alt'],
            })

        output_json(images)

    asyncio.run(_extract_images())


@app.command()
def table(
    selector: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    headers: Optional[str] = typer.Option(None, help='Comma-separated header names, or "auto" to detect'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode (overrides global)'),
):
    """Extract table data as JSON."""
    import asyncio

    async def _extract_table():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        # Extract table using JavaScript
        table_data = await connection.page.evaluate(f'''
            (() => {{
                const table = document.querySelector('{selector}');
                if (!table) return {{ error: 'Table not found' }};
                    
                const rows = Array.from(table.querySelectorAll('tr'));
                const headerRow = rows[0];
                const headerCells = Array.from(headerRow.querySelectorAll('th, td'));
                const headerNames = headerCells.map(cell => cell.textContent.trim());
                    
                const dataRows = rows.slice(1);
                const data = dataRows.map(row => {{
                    const cells = Array.from(row.querySelectorAll('td'));
                    const rowData = {{}};
                    headerNames.forEach((header, index) => {{
                        rowData[header] = cells[index] ? cells[index].textContent.trim() : '';
                    }});
                    return rowData;
                }});
                    
                return {{
                    headers: headerNames,
                    rows: data
                }};
            }})()
        ''')

        if headers and headers != 'auto':
            # Use provided headers
            header_list = [h.strip() for h in headers.split(',')]
            table_data['headers'] = header_list

        output_json(table_data)

    asyncio.run(_extract_table())


@app.command()
def social(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Extract Open Graph and Twitter Card meta tags."""
    import asyncio

    async def _social():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        social_data = await connection.page.evaluate('''
            () => {
                const getMeta = (name) => {
                    const meta = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
                    return meta ? meta.content : null;
                };
                
                return {
                    openGraph: {
                        title: getMeta('og:title'),
                        description: getMeta('og:description'),
                        image: getMeta('og:image'),
                        url: getMeta('og:url'),
                        type: getMeta('og:type'),
                        siteName: getMeta('og:site_name'),
                        locale: getMeta('og:locale')
                    },
                    twitter: {
                        card: getMeta('twitter:card'),
                        title: getMeta('twitter:title'),
                        description: getMeta('twitter:description'),
                        image: getMeta('twitter:image'),
                        site: getMeta('twitter:site'),
                        creator: getMeta('twitter:creator')
                    }
                };
            }
        ''')
        
        output_json({'social': social_data, 'url': connection.page.url})

    asyncio.run(_social())


@app.command()
def table_csv(
    selector: str,
    output_file: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Extract HTML table and save directly to CSV."""
    import asyncio

    async def _table_csv():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')

        table_data = await connection.page.evaluate(f'''
            (() => {{
                const table = document.querySelector('{selector}');
                if (!table) return {{ error: 'Table not found' }};
                    
                const rows = Array.from(table.querySelectorAll('tr'));
                const data = rows.map(row => {{
                    const cells = Array.from(row.querySelectorAll('th, td'));
                    return cells.map(cell => cell.textContent.trim());
                }});
                    
                return data;
            }})()
        ''')

        if 'error' in table_data:
            output_json(table_data)
            return

        # Write to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(table_data)
        
        output_json({
            'message': f'Table exported to {output_file}',
            'rows': len(table_data)
        })

    asyncio.run(_table_csv())
