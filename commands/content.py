"""Content extraction and transformation commands."""

import typer
import json
import re
from typing import Optional, List, Dict, Any, Literal
from core.browser import get_or_create_connection, get_browser_manager
from core import settings

app = typer.Typer()

# Valid wait_until values for Playwright
WaitUntilType = Literal['domcontentloaded', 'load', 'networkidle', 'commit']


def output_json(data: dict):
    """Output JSON data."""
    if not settings.quiet:
        print(json.dumps(data, indent=2))


async def expand_collapsible_elements(page, content_selector: str = None) -> dict:
    """Expand all collapsible elements on the page (details, accordions, FAQs, etc.).
    
    Args:
        page: Playwright page object
        content_selector: Optional CSS selector to limit expansion to main content area.
                         If not provided, auto-detects main/article to avoid nav elements.
    """
    result = await page.evaluate('''
        (contentSelector) => {
            let expanded = 0;
            let errors = [];
            
            // Determine the content container to avoid expanding navigation elements
            let container = document.body;
            if (contentSelector) {
                const el = document.querySelector(contentSelector);
                if (el) container = el;
            } else {
                // Auto-detect main content area to avoid navigation
                const mainSelectors = ['main', 'article', '[role="main"]', '.main-content', '#content'];
                for (const sel of mainSelectors) {
                    const el = document.querySelector(sel);
                    if (el && el.textContent.trim().length > 200) {
                        container = el;
                        break;
                    }
                }
            }
            
            // Helper to check if element is likely navigation
            const isNavigation = (el) => {
                const nav = el.closest('nav, [role="navigation"], header, aside, .sidebar, .nav, .menu');
                return !!nav;
            };
            
            // 1. Expand all <details> elements within container
            container.querySelectorAll('details:not([open])').forEach(el => {
                try {
                    el.open = true;
                    expanded++;
                } catch (e) { errors.push('details: ' + e.message); }
            });
            
            // 2. Click elements with aria-expanded="false" (only non-navigation)
            container.querySelectorAll('[aria-expanded="false"]').forEach(el => {
                if (isNavigation(el)) return;
                if (el.tagName === 'A' || el.closest('a[href]')) return;
                try {
                    el.click();
                    expanded++;
                } catch (e) { errors.push('aria-expanded: ' + e.message); }
            });
            
            // 3. Click summary elements (for details that might not have open attribute)
            container.querySelectorAll('summary').forEach(el => {
                try {
                    const details = el.closest('details');
                    if (details && !details.open) {
                        el.click();
                        expanded++;
                    }
                } catch (e) { errors.push('summary: ' + e.message); }
            });
            
            // 4. Click buttons with aria-controls (accordion patterns) - skip nav
            container.querySelectorAll('button[aria-controls]').forEach(el => {
                if (isNavigation(el)) return;
                try {
                    if (el.getAttribute('aria-expanded') === 'false') {
                        el.click();
                        expanded++;
                    }
                } catch (e) { errors.push('aria-controls: ' + e.message); }
            });
            
            // 5. Expand common accordion/collapse classes
            const collapseSelectors = [
                '.collapsed', '.accordion-button.collapsed',
                '[data-bs-toggle="collapse"]:not(.show)',
                '.collapsible:not(.active)', '.expandable:not(.expanded)'
            ];
            collapseSelectors.forEach(selector => {
                container.querySelectorAll(selector).forEach(el => {
                    if (isNavigation(el)) return;
                    try {
                        el.click();
                        expanded++;
                    } catch (e) {}
                });
            });
            
            // 6. Click "show more", "read more", "expand" buttons (ONLY buttons, not links)
            const expandTexts = ['show more', 'read more', 'expand all', 'see all', 'load more', 'view all'];
            container.querySelectorAll('button, [role="button"]').forEach(el => {
                if (isNavigation(el)) return;
                if (el.tagName === 'A' || el.closest('a') || el.hasAttribute('href')) return;
                
                const text = (el.textContent || '').toLowerCase().trim();
                if (expandTexts.some(t => text === t || text.startsWith(t + ' ') || text.endsWith(' ' + t))) {
                    try {
                        el.click();
                        expanded++;
                    } catch (e) {}
                }
            });
            
            return { expanded, errors: errors.slice(0, 5), container: container.tagName };
        }
    ''', content_selector)
    return result


@app.command()
def strip(
    selector: Optional[str] = typer.Option(None, help='CSS selector (default: body)'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    wait_until: str = typer.Option('domcontentloaded', '--wait-until', '-w', help='Wait until: domcontentloaded, load, networkidle, commit'),
    expand: bool = typer.Option(False, '--expand', '-e', help='Expand all collapsible elements before extraction'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Strip HTML and extract clean readable text."""
    import asyncio

    async def _strip():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until=wait_until, timeout=settings.timeout)

            # Expand collapsible elements if requested
            if expand:
                await expand_collapsible_elements(connection.page)
                await connection.page.wait_for_timeout(500)  # Brief wait for animations

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
    wait_until: str = typer.Option('domcontentloaded', '--wait-until', '-w', help='Wait until: domcontentloaded, load, networkidle, commit'),
    expand: bool = typer.Option(False, '--expand', '-e', help='Expand all collapsible elements before extraction'),
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
                await connection.page.goto(url, wait_until=wait_until, timeout=settings.timeout)

            # Expand collapsible elements if requested
            if expand:
                await expand_collapsible_elements(connection.page)
                await connection.page.wait_for_timeout(500)  # Brief wait for animations

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


@app.command()
def expand(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to first'),
    wait_until: str = typer.Option('networkidle', '--wait-until', '-w', help='Wait until: domcontentloaded, load, networkidle, commit'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Expand all collapsible elements on the page (details, accordions, FAQs, etc.)."""
    import asyncio

    async def _expand():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            if url:
                await connection.page.goto(url, wait_until=wait_until, timeout=settings.timeout)

            result = await expand_collapsible_elements(connection.page)
            await connection.page.wait_for_timeout(500)  # Brief wait for animations
            
            output_json({
                'message': f'Expanded {result["expanded"]} collapsible elements',
                'expanded_count': result['expanded'],
                'errors': result.get('errors', [])
            })
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_expand())


@app.command()
def smart(
    url: str = typer.Argument(..., help='URL to scrape'),
    selector: Optional[str] = typer.Option(None, '--selector', '-s', help='CSS selector for main content (auto-detected if not provided)'),
    output: Optional[str] = typer.Option(None, '--output', '-o', help='Output file path'),
    format: str = typer.Option('text', '--format', '-f', help='Output format: text, markdown, html, json'),
    no_expand: bool = typer.Option(False, '--no-expand', help='Skip expanding collapsible elements'),
    wait_timeout: int = typer.Option(3000, '--wait-timeout', help='Additional wait time after page load (ms)'),
    wait_for: Optional[str] = typer.Option(None, '--wait-for', help='CSS selector to wait for before extraction (for SPA routes)'),
    wait_for_text: Optional[str] = typer.Option(None, '--wait-for-text', help='Text content to wait for before extraction'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: Optional[bool] = typer.Option(None, '--headless/--headed', help='Run in headless mode'),
):
    """Smart scrape: handles SPAs, expands content, extracts clean text.
    
    Designed for modern JavaScript-heavy sites (React, Next.js, Vue, etc.)
    that require special handling for dynamic content.
    
    Use --wait-for to specify a CSS selector that must appear before extraction.
    Use --wait-for-text to wait for specific text content to appear on the page.
    """
    import asyncio
    import markdownify
    import html2text

    async def _smart():
        connection = await get_or_create_connection(session_id, headless=headless if headless is not None else settings.headless)
        try:
            # Step 1: Navigate with networkidle to wait for JS to finish
            await connection.page.goto(url, wait_until='networkidle', timeout=settings.timeout)
            
            # Step 1b: Wait for specific selector if provided (for SPA routes)
            if wait_for:
                await connection.page.wait_for_selector(wait_for, timeout=settings.timeout)
            
            # Step 1c: Wait for specific text if provided
            if wait_for_text:
                await connection.page.wait_for_function(
                    f'document.body.innerText.includes({json.dumps(wait_for_text)})',
                    timeout=settings.timeout
                )
            
            # Step 2: Additional wait for any lazy-loaded content
            await connection.page.wait_for_timeout(wait_timeout)
            
            # Step 3: Expand collapsible elements (unless disabled)
            expanded_count = 0
            if not no_expand:
                result = await expand_collapsible_elements(connection.page)
                expanded_count = result.get('expanded', 0)
                if expanded_count > 0:
                    await connection.page.wait_for_timeout(1000)  # Wait for expanded content
            
            # Step 4: Auto-detect main content selector if not provided
            content_selector = selector
            if not content_selector:
                content_selector = await connection.page.evaluate('''
                    () => {
                        // Priority list of common main content selectors
                        const selectors = [
                            'main article', 'article', 'main', 
                            '[role="main"]', '.main-content', '#main-content',
                            '.content', '#content', '.article', '#article',
                            '.post-content', '.entry-content', '.page-content'
                        ];
                        for (const sel of selectors) {
                            const el = document.querySelector(sel);
                            if (el && el.textContent.trim().length > 200) {
                                return sel;
                            }
                        }
                        return 'body';
                    }
                ''')
            
            # Step 5: Extract content
            if content_selector == 'body':
                html_content = await connection.page.content()
            else:
                try:
                    html_content = await connection.page.locator(content_selector).first.inner_html()
                except:
                    html_content = await connection.page.content()
            
            # Step 6: Get page metadata
            title = await connection.page.title()
            page_url = connection.page.url
            
            # Step 7: Format output
            if format == 'html':
                final_content = html_content
            elif format == 'markdown':
                final_content = markdownify.markdownify(html_content, heading_style='ATX')
            elif format == 'json':
                h = html2text.HTML2Text()
                h.ignore_links = False
                h.ignore_images = False
                h.body_width = 0
                text_content = h.handle(html_content).strip()
                
                json_output = {
                    'url': page_url,
                    'title': title,
                    'selector_used': content_selector,
                    'expanded_elements': expanded_count,
                    'content': text_content,
                    'content_length': len(text_content),
                    'word_count': len(text_content.split())
                }
                final_content = json.dumps(json_output, indent=2)
            else:  # text
                h = html2text.HTML2Text()
                h.ignore_links = False
                h.ignore_images = False
                h.body_width = 0
                final_content = h.handle(html_content).strip()
            
            # Step 8: Output
            if output:
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(final_content)
                output_json({
                    'message': f'Content saved to {output}',
                    'url': page_url,
                    'title': title,
                    'selector_used': content_selector,
                    'expanded_elements': expanded_count,
                    'format': format,
                    'content_length': len(final_content),
                    'word_count': len(final_content.split()) if format in ['text', 'markdown'] else None
                })
            else:
                if not settings.quiet:
                    print(final_content)
                    
        except Exception as e:
            output_json({'error': str(e)})

    asyncio.run(_smart())
