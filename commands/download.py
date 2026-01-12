"""Download and export commands."""

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
def file(
    selector: Optional[str] = typer.Option(None, help='CSS selector of download link/button'),
    url: Optional[str] = typer.Option(None, help='Direct URL to download'),
    output_dir: str = typer.Option('./downloads', '--output-dir', '-o', help='Output directory'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Download file from URL or trigger download button."""
    import asyncio

    async def _download():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)
                download_url = url
            elif selector:
                download_url = await connection.page.locator(selector).first.get_attribute('href')
                if not download_url:
                    output_json({'error': f'No href found for {selector}'})
                    return
            else:
                output_json({'error': 'Must provide either --url or --selector'})
                return

            os.makedirs(output_dir, exist_ok=True)

            # Wait for download
            async with connection.page.expect_download() as download_info:
                if selector:
                    await connection.page.locator(selector).first.click()
                else:
                    await connection.page.goto(download_url)

            download = await download_info.value
            filename = download.suggested_filename()
            filepath = os.path.join(output_dir, filename)
            await download.save_as(filepath)

            output_json({'message': f'Downloaded to {filepath}', 'filename': filename})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_download())


@app.command()
def export(
    data_type: str = typer.Argument(..., help='Data type: links, images, text, etc.'),
    selector: Optional[str] = typer.Option(None, help='CSS selector'),
    output: str = typer.Option('export.json', '--output', '-o', help='Output file path'),
    format: str = typer.Option('json', help='Output format: json, csv, yaml'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Export extracted data to file."""
    import asyncio
    import csv
    import yaml

    async def _export():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)

            data = None

            if data_type == 'links':
                links = await connection.page.evaluate('''
                    Array.from(document.querySelectorAll('a'))
                        .map(a => ({href: a.href, text: a.textContent?.trim() || ''}))
                        .filter(link => link.href)
                ''')
                data = links
            elif data_type == 'images':
                images = await connection.page.evaluate('''
                    Array.from(document.querySelectorAll('img'))
                        .map(img => ({src: img.src, alt: img.alt || ''}))
                        .filter(img => img.src)
                ''')
                data = images
            elif data_type == 'text' and selector:
                text = await connection.page.locator(selector).first.text_content()
                data = text
            else:
                output_json({'error': f'Unknown data type: {data_type}'})
                return

            # Write to file
            if format == 'csv' and isinstance(data, list):
                with open(output, 'w', newline='', encoding='utf-8') as f:
                    if data and isinstance(data[0], dict):
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
            elif format == 'yaml':
                with open(output, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False)
            else:  # json
                with open(output, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

            output_json({'message': f'Exported to {output}', 'format': format, 'items': len(data) if isinstance(data, list) else 1})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_export())


@app.command()
def save_html(
    output: str = typer.Option('page.html', '--output', '-o', help='Output file path'),
    selector: Optional[str] = typer.Option(None, help='CSS selector (default: full page)'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Save current page HTML to file."""
    import asyncio

    async def _save_html():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)

            if selector:
                html = await connection.page.locator(selector).first.inner_html()
            else:
                html = await connection.page.content()

            with open(output, 'w', encoding='utf-8') as f:
                f.write(html)

            output_json({'message': f'HTML saved to {output}'})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_save_html())
