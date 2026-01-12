"""Content extraction and transformation commands."""

import typer
import json
import re
from typing import Optional, List, Dict, Any
from core.browser import get_or_create_connection, get_browser_manager
from core import settings

app = typer.Typer()


def output_json(data: dict):
    """Output JSON data."""
    if not settings.quiet:
        print(json.dumps(data, indent=2))


@app.command()
def strip(
    selector: Optional[str] = typer.Option(None, help='CSS selector (default: body)'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Strip HTML and extract clean readable text."""
    import asyncio

    async def _strip():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)

            if selector:
                html = await connection.page.locator(selector).first.inner_html()
            else:
                html = await connection.page.content()

            # Strip HTML and get clean text
            import html2text
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = False
            h.body_width = 0  # Don't wrap lines
            text = h.handle(html).strip()

            if not settings.quiet:
                print(text)
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_strip())


@app.command()
def markdown(
    selector: Optional[str] = typer.Option(None, help='CSS selector (default: body)'),
    output: Optional[str] = typer.Option(None, '--output', '-o', help='Output file path'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Convert page or element to Markdown."""
    import asyncio
    import markdownify

    async def _markdown():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)

            if selector:
                html = await connection.page.locator(selector).first.inner_html()
            else:
                html = await connection.page.content()

            md = markdownify.markdownify(html, heading_style='ATX')

            if output:
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(md)
                output_json({'message': f'Markdown saved to {output}'})
            else:
                if not settings.quiet:
                    print(md)
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_markdown())


@app.command()
def meta(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Extract meta tags (title, description, og:*, twitter:*)."""
    import asyncio

    async def _meta():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)

            meta_data = await connection.page.evaluate('''
                () => {
                    const meta = {};
                    const tags = document.querySelectorAll('meta');
                    tags.forEach(tag => {
                        const name = tag.getAttribute('name') || tag.getAttribute('property') || tag.getAttribute('itemprop');
                        const content = tag.getAttribute('content');
                        if (name && content) {
                            meta[name] = content;
                        }
                    });
                    meta.title = document.title;
                    return meta;
                }
            ''')

            output_json(meta_data)
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_meta())


@app.command()
def schema(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Extract structured data (JSON-LD, microdata, RDFa)."""
    import asyncio

    async def _schema():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)

            schemas = await connection.page.evaluate('''
                () => {
                    const results = {};
                    
                    // JSON-LD
                    const jsonLd = [];
                    document.querySelectorAll('script[type="application/ld+json"]').forEach(script => {
                        try {
                            jsonLd.push(JSON.parse(script.textContent));
                        } catch (e) {}
                    });
                    if (jsonLd.length > 0) results.jsonLd = jsonLd;
                    
                    // Microdata
                    const microdata = [];
                    document.querySelectorAll('[itemscope]').forEach(item => {
                        const data = {};
                        const type = item.getAttribute('itemtype');
                        if (type) data.type = type;
                        item.querySelectorAll('[itemprop]').forEach(prop => {
                            const name = prop.getAttribute('itemprop');
                            const value = prop.getAttribute('content') || prop.textContent?.trim();
                            if (name && value) data[name] = value;
                        });
                        if (Object.keys(data).length > 0) microdata.push(data);
                    });
                    if (microdata.length > 0) results.microdata = microdata;
                    
                    return results;
                }
            ''')

            output_json(schemas)
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_schema())


@app.command()
def xpath(
    xpath: str = typer.Argument(..., help='XPath expression'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    attribute: Optional[str] = typer.Option(None, help='Extract attribute value'),
    text: bool = typer.Option(False, '--text/--html', help='Extract text content (default: HTML)'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Query elements by XPath."""
    import asyncio

    async def _xpath():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)

            # Build JavaScript function with parameters embedded
            js_code = f'''
                (() => {{
                    const xpath = {json.dumps(xpath)};
                    const attribute = {json.dumps(attribute or '')};
                    const textMode = {json.dumps(text)};
                    const result = [];
                    try {{
                        const nodes = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                        for (let i = 0; i < nodes.snapshotLength; i++) {{
                            const node = nodes.snapshotItem(i);
                            if (node) {{
                                if (attribute) {{
                                    result.push(node.getAttribute(attribute) || '');
                                }} else if (textMode) {{
                                    result.push(node.textContent?.trim() || '');
                                }} else {{
                                    result.push(node.outerHTML);
                                }}
                            }}
                        }}
                    }} catch (e) {{
                        return {{error: e.message}};
                    }}
                    return result;
                }})()
            '''
            results = await connection.page.evaluate(js_code)

            if len(results) == 1:
                output_json({'result': results[0]})
            else:
                output_json({'results': results})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_xpath())


@app.command()
def regex(
    pattern: str = typer.Argument(..., help='Regex pattern'),
    selector: Optional[str] = typer.Option(None, help='CSS selector (default: body)'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Extract text matching regex pattern."""
    import asyncio

    async def _regex():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)

            if selector:
                text = await connection.page.locator(selector).first.text_content()
            else:
                text = await connection.page.evaluate('document.body.textContent')

            matches = re.findall(pattern, text or '', re.MULTILINE | re.DOTALL)

            if len(matches) == 1:
                output_json({'match': matches[0]})
            else:
                output_json({'matches': matches})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_regex())


@app.command()
def forms(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """List all forms with their fields and actions."""
    import asyncio

    async def _forms():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout)

            forms_data = await connection.page.evaluate('''
                () => {
                    const forms = [];
                    document.querySelectorAll('form').forEach((form, index) => {
                        const formData = {
                            index: index,
                            id: form.id || null,
                            name: form.name || null,
                            action: form.action || null,
                            method: form.method || 'get',
                            fields: []
                        };
                        
                        form.querySelectorAll('input, textarea, select').forEach(field => {
                            const fieldData = {
                                type: field.type || field.tagName.toLowerCase(),
                                name: field.name || null,
                                id: field.id || null,
                                placeholder: field.placeholder || null,
                                required: field.required || false,
                                value: field.value || null
                            };
                            if (field.tagName === 'SELECT') {
                                fieldData.options = Array.from(field.options).map(opt => ({
                                    value: opt.value,
                                    text: opt.text
                                }));
                            }
                            formData.fields.push(fieldData);
                        });
                        
                        forms.push(formData);
                    });
                    return forms;
                }
            ''')

            output_json({'forms': forms_data})
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_forms())
