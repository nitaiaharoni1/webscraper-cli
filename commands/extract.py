"""Extraction commands."""

import csv
import json
import re
import sys
from typing import Any, Dict, List, Literal, Optional

import typer

from core.async_command import get_connection, run_async
from core.output import output, output_json, output_text
from core.settings import settings

app = typer.Typer()


@app.command()
def text(
    selector: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    all: bool = typer.Option(False, "--all/--first", help="Extract from all matching elements"),
    format: Optional[str] = typer.Option(None, help="Output format: json, csv, plain, table (overrides global)"),
    wait_for: Optional[str] = typer.Option(None, "--wait-for", help="Wait for CSS selector before extracting"),
    wait_for_text: Optional[str] = typer.Option(
        None, "--wait-for-text", help="Wait until this text appears in the page before extracting"
    ),
    settle_time: int = typer.Option(
        0, "--settle-time", help="Extra ms to wait after page load before extracting (useful for SPAs)"
    ),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(
        None, "--headless/--headed", help="Run in headless mode (overrides global)"
    ),
):
    """Extract text from elements matching selector.

    Extracts text content from elements on the page. Can extract from a single
    element or all matching elements.

    Examples:
        cli.py extract text "h1" --url https://example.com
        cli.py extract text "p" --all --url https://example.com
        cli.py extract text ".title" --format plain
    """

    async def _extract_text():
        connection = await get_connection(session_id, headless, url)
        if wait_for:
            await connection.page.wait_for_selector(wait_for, timeout=settings.timeout)
        if wait_for_text:
            await connection.page.wait_for_function(
                f"document.body.innerText.includes({json.dumps(wait_for_text)})",
                timeout=settings.timeout,
            )
        if settle_time > 0:
            await connection.page.wait_for_timeout(settle_time)

        # Optimize bulk extraction with single JS call
        if all:
            # Single JS call to extract all matching elements
            result = await connection.page.evaluate(f"""
                Array.from(document.querySelectorAll('{selector}'))
                    .map(el => el.textContent?.trim() || '')
                    .filter(text => text)
            """)
        else:
            # Single JS call for first element
            result = await connection.page.evaluate(f"""
                (() => {{
                    const el = document.querySelector('{selector}');
                    return el ? el.textContent?.trim() || '' : '';
                }})()
            """)

        output(result, format=format)

    run_async(_extract_text())


@app.command()
def links(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    selector: Optional[str] = typer.Option("a", help="CSS selector for links"),
    absolute: bool = typer.Option(False, "--absolute/--relative", help="Convert relative URLs to absolute"),
    format: Optional[str] = typer.Option(None, help="Output format: json, csv, plain, table"),
    wait_for: Optional[str] = typer.Option(None, "--wait-for", help="Wait for CSS selector before extracting"),
    wait_for_text: Optional[str] = typer.Option(
        None, "--wait-for-text", help="Wait until this text appears in the page before extracting"
    ),
    settle_time: int = typer.Option(
        0, "--settle-time", help="Extra ms to wait after page load before extracting (useful for SPAs)"
    ),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(
        None, "--headless/--headed", help="Run in headless mode (overrides global)"
    ),
):
    """Extract links from page."""

    async def _extract_links():
        connection = await get_connection(session_id, headless, url)
        if wait_for:
            await connection.page.wait_for_selector(wait_for, timeout=settings.timeout)
        if wait_for_text:
            await connection.page.wait_for_function(
                f"document.body.innerText.includes({json.dumps(wait_for_text)})",
                timeout=settings.timeout,
            )
        if settle_time > 0:
            await connection.page.wait_for_timeout(settle_time)

        # Optimize with single JS call
        base_url = connection.page.url
        links_data = await connection.page.evaluate(f"""
            Array.from(document.querySelectorAll('{selector}'))
                .map(el => ({{
                    href: el.getAttribute('href') || '',
                    text: el.textContent?.trim() || ''
                }}))
                .filter(link => link.href)
        """)

        links = []
        for link_data in links_data:
            href = link_data["href"]
            if absolute and not href.startswith(("http://", "https://")):
                from urllib.parse import urljoin

                href = urljoin(base_url, href)
            links.append(
                {
                    "href": href,
                    "text": link_data["text"],
                }
            )

        output(links, format=format or settings.format)

    run_async(_extract_links())


@app.command()
def html(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    selector: Optional[str] = typer.Option(None, help="CSS selector (extracts innerHTML if specified)"),
    outer: bool = typer.Option(False, "--outer/--inner", help="Extract outerHTML instead of innerHTML"),
    wait_for: Optional[str] = typer.Option(None, "--wait-for", help="Wait for CSS selector before extracting"),
    wait_for_text: Optional[str] = typer.Option(
        None, "--wait-for-text", help="Wait until this text appears in the page before extracting"
    ),
    settle_time: int = typer.Option(
        0, "--settle-time", help="Extra ms to wait after page load before extracting (useful for SPAs)"
    ),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(
        None, "--headless/--headed", help="Run in headless mode (overrides global)"
    ),
):
    """Extract HTML content."""

    async def _extract_html():
        connection = await get_connection(session_id, headless, url)
        if wait_for:
            await connection.page.wait_for_selector(wait_for, timeout=settings.timeout)
        if wait_for_text:
            await connection.page.wait_for_function(
                f"document.body.innerText.includes({json.dumps(wait_for_text)})",
                timeout=settings.timeout,
            )
        if settle_time > 0:
            await connection.page.wait_for_timeout(settle_time)

        if selector:
            element = connection.page.locator(selector).first
            if outer:
                html_content = await element.evaluate("el => el.outerHTML")
            else:
                html_content = await element.evaluate("el => el.innerHTML")
        else:
            html_content = await connection.page.content()

        output_text(html_content)

    run_async(_extract_html())


@app.command()
def attr(
    selector: str,
    attribute: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    all: bool = typer.Option(False, "--all/--first", help="Extract from all matching elements"),
    format: str = typer.Option("json", help="Output format: json, plain"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(
        None, "--headless/--headed", help="Run in headless mode (overrides global)"
    ),
):
    """Extract attribute value from elements."""

    async def _extract_attr():
        connection = await get_connection(session_id, headless, url)

        # Optimize with single JS call
        if all:
            result = await connection.page.evaluate(f"""
                Array.from(document.querySelectorAll('{selector}'))
                    .map(el => el.getAttribute('{attribute}'))
                    .filter(attr => attr)
            """)
        else:
            result = await connection.page.evaluate(f"""
                (() => {{
                    const el = document.querySelector('{selector}');
                    return el ? el.getAttribute('{attribute}') || '' : '';
                }})()
            """)

        output(result, format=format)

    run_async(_extract_attr())


@app.command()
def count(
    selector: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(
        None, "--headless/--headed", help="Run in headless mode (overrides global)"
    ),
):
    """Count elements matching selector."""

    async def _count():
        connection = await get_connection(session_id, headless, url)

        locator = connection.page.locator(selector)
        count_value = await locator.count()
        output_json({"count": count_value, "selector": selector})

    run_async(_count())


@app.command()
def images(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    selector: Optional[str] = typer.Option("img", help="CSS selector for images"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(
        None, "--headless/--headed", help="Run in headless mode (overrides global)"
    ),
):
    """Extract image URLs from page."""

    async def _extract_images():
        connection = await get_connection(session_id, headless, url)

        # Optimize with single JS call
        base_url = connection.page.url
        images_data = await connection.page.evaluate(f"""
            Array.from(document.querySelectorAll('{selector}'))
                .map(el => ({{
                    src: el.getAttribute('src') || '',
                    alt: el.getAttribute('alt') || ''
                }}))
                .filter(img => img.src)
        """)

        images = []
        for img_data in images_data:
            src = img_data["src"]
            if not src.startswith(("http://", "https://", "data:")):
                from urllib.parse import urljoin

                src = urljoin(base_url, src)
            images.append(
                {
                    "src": src,
                    "alt": img_data["alt"],
                }
            )

        output_json(images)

    run_async(_extract_images())


_TABLE_FALLBACK_SELECTORS = [
    ".wikitable",
    ".sortable",
    ".dataframe",
    "table.data",
    '[role="table"]',
    ".table",
    "table[class]",
    "table",
]


def _make_extract_table_js(selector: str) -> str:
    """Build a self-contained IIFE that extracts one table by exact selector string."""
    sel_json = json.dumps(selector)
    return f"""
        (() => {{
            const table = document.querySelector({sel_json});
            if (!table) return {{ error: 'Table not found' }};
            const rows = Array.from(table.querySelectorAll('tr'));
            if (!rows.length) return {{ headers: [], rows: [] }};
            const headerNames = Array.from(rows[0].querySelectorAll('th, td'))
                .map(c => c.textContent.trim());
            const data = rows.slice(1).map(row => {{
                const cells = Array.from(row.querySelectorAll('td'));
                const rowData = {{}};
                headerNames.forEach((h, i) => {{ rowData[h] = cells[i] ? cells[i].textContent.trim() : ''; }});
                return rowData;
            }});
            return {{ headers: headerNames, rows: data }};
        }})()
    """


def _make_extract_all_tables_js(selector: str) -> str:
    """Build a self-contained IIFE that extracts every table matching selector."""
    sel_json = json.dumps(selector)
    return f"""
        (() => {{
            function extractOne(table) {{
                const rows = Array.from(table.querySelectorAll('tr'));
                if (!rows.length) return {{ headers: [], rows: [] }};
                const headerNames = Array.from(rows[0].querySelectorAll('th, td'))
                    .map(c => c.textContent.trim());
                const data = rows.slice(1).map(row => {{
                    const cells = Array.from(row.querySelectorAll('td'));
                    const rowData = {{}};
                    headerNames.forEach((h, i) => {{ rowData[h] = cells[i] ? cells[i].textContent.trim() : ''; }});
                    return rowData;
                }});
                return {{ headers: headerNames, rows: data }};
            }}
            return Array.from(document.querySelectorAll({sel_json})).map(extractOne);
        }})()
    """


@app.command()
def table(
    selector: Optional[str] = typer.Argument(None, help="CSS selector for table (auto-detects if omitted)"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    headers: Optional[str] = typer.Option(None, help='Comma-separated header names, or "auto" to detect'),
    all: bool = typer.Option(False, "--all/--first", help="Extract all matching tables"),
    wait_for: Optional[str] = typer.Option(None, "--wait-for", help="Wait for CSS selector before extracting"),
    wait_for_text: Optional[str] = typer.Option(
        None, "--wait-for-text", help="Wait until this text appears before extracting"
    ),
    settle_time: int = typer.Option(0, "--settle-time", help="Extra ms to wait after page load (useful for SPAs)"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(
        None, "--headless/--headed", help="Run in headless mode (overrides global)"
    ),
):
    """Extract table data as JSON. Auto-detects tables if no selector is given.

    When a selector is provided but matches nothing, falls back to auto-detection
    and includes a note in the output. Use --all to extract every table on the page.

    Examples:
        cli.py extract table --url https://example.com
        cli.py extract table "table.data" --url https://example.com
        cli.py extract table --all --url https://en.wikipedia.org/wiki/Python_(programming_language)
    """

    async def _extract_table():
        connection = await get_connection(session_id, headless, url)

        if wait_for:
            await connection.page.wait_for_selector(wait_for, timeout=settings.timeout)
        if wait_for_text:
            await connection.page.wait_for_function(
                f"document.body.innerText.includes({json.dumps(wait_for_text)})",
                timeout=settings.timeout,
            )
        if settle_time > 0:
            await connection.page.wait_for_timeout(settle_time)

        if all:
            effective_sel = selector or "table"
            results = await connection.page.evaluate(_make_extract_all_tables_js(effective_sel))
            if headers and headers != "auto":
                header_list = [h.strip() for h in headers.split(",")]
                for t in results:
                    t["headers"] = header_list
            output_json(results)
            return

        # --- Single table with fallback chain ---
        def _has_content(t: Any) -> bool:
            """A table result is useful only if it has at least one data row."""
            return isinstance(t, dict) and "error" not in t and bool(t.get("rows"))

        note = None
        effective_sel = selector

        if selector:
            result = await connection.page.evaluate(_make_extract_table_js(selector))
            if not _has_content(result):
                # Provided selector matched nothing or yielded empty data — try fallbacks
                for fallback in _TABLE_FALLBACK_SELECTORS:
                    candidate = await connection.page.evaluate(_make_extract_table_js(fallback))
                    if _has_content(candidate):
                        note = f"Selector '{selector}' not found — used auto-detected '{fallback}' instead"
                        effective_sel = fallback
                        result = candidate
                        break
                if not _has_content(result):
                    table_count = await connection.page.evaluate("() => document.querySelectorAll('table').length")
                    output_json(
                        {
                            "error": f"No table found with selector '{selector}' or any fallback",
                            "tables_on_page": table_count,
                            "suggestion": "Omit the selector to auto-detect, or add --all to list all tables",
                        }
                    )
                    return
            table_data = result
        else:
            # Auto-detect: find first matching table with actual content
            table_data = None
            for fallback in _TABLE_FALLBACK_SELECTORS:
                candidate = await connection.page.evaluate(_make_extract_table_js(fallback))
                if _has_content(candidate):
                    effective_sel = fallback
                    table_data = candidate
                    break
            if table_data is None:
                table_count = await connection.page.evaluate("() => document.querySelectorAll('table').length")
                output_json(
                    {
                        "error": "No table found on page",
                        "tables_on_page": table_count,
                        "suggestion": "Try 'webscraper extract html' to inspect page structure",
                    }
                )
                return

        if headers and headers != "auto":
            header_list = [h.strip() for h in headers.split(",")]
            table_data["headers"] = header_list

        if note:
            table_data["note"] = note

        output_json(table_data)

    run_async(_extract_table())


@app.command()
def table_csv(
    selector: str,
    output_file: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Extract HTML table and save directly to CSV."""

    async def _table_csv():
        connection = await get_connection(session_id, headless, url)

        table_data = await connection.page.evaluate(f"""
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
        """)

        if "error" in table_data:
            output_json(table_data)
            return

        # Write to CSV
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(table_data)

        output_json({"message": f"Table exported to {output_file}", "rows": len(table_data)})

    run_async(_table_csv())


@app.command()
def records(
    container: str = typer.Argument(
        ..., help="CSS selector for repeating container elements (e.g. 'article', 'li.item')"
    ),
    fields: str = typer.Option(
        ...,
        "--fields",
        "-f",
        help='JSON mapping of field names to sub-selectors, e.g. \'{"name": "h2 a", "desc": "p"}\'',
    ),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    wait_for: Optional[str] = typer.Option(None, "--wait-for", help="Wait for CSS selector before extracting"),
    wait_for_text: Optional[str] = typer.Option(
        None, "--wait-for-text", help="Wait until this text appears before extracting"
    ),
    settle_time: int = typer.Option(0, "--settle-time", help="Extra ms to wait after page load (useful for SPAs)"),
    format: Optional[str] = typer.Option(None, help="Output format: json, csv, plain, table"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(
        None, "--headless/--headed", help="Run in headless mode (overrides global)"
    ),
):
    """Extract structured records from repeating page elements.

    Maps multiple sub-selectors per container element into a JSON array of objects.
    Ideal for listings, cards, search results, and any repeating structure.

    Examples:
        cli.py extract records "article" --fields '{"name":"h2 a","desc":"p","stars":".stars"}' --url https://github.com/trending
        cli.py extract records "tr" --fields '{"name":"td:nth-child(1)","value":"td:nth-child(2)"}' --url https://example.com
    """

    async def _extract_records():
        connection = await get_connection(session_id, headless, url)

        if wait_for:
            await connection.page.wait_for_selector(wait_for, timeout=settings.timeout)
        if wait_for_text:
            await connection.page.wait_for_function(
                f"document.body.innerText.includes({json.dumps(wait_for_text)})",
                timeout=settings.timeout,
            )
        if settle_time > 0:
            await connection.page.wait_for_timeout(settle_time)

        try:
            field_map = json.loads(fields)
        except json.JSONDecodeError as exc:
            output_json({"error": f"--fields must be valid JSON: {exc}"})
            return

        # Build field extraction JS: iterate containers, query each sub-selector inside.
        # Supports multiple comma-separated selectors per field as fallback chain.
        # Also uses aria-label and data attributes as fallbacks when querySelector returns null.
        field_entries_js = ", ".join(f"[{json.dumps(k)}, {json.dumps(v)}]" for k, v in field_map.items())
        container_json = json.dumps(container)

        js = f"""
            (() => {{
                const fieldMap = new Map([{field_entries_js}]);
                return Array.from(document.querySelectorAll({container_json})).map(el => {{
                    const record = {{}};
                    fieldMap.forEach((subSel, key) => {{
                        let text = null;
                        // Try each comma-separated selector as a fallback chain
                        const selectors = subSel.split(',').map(s => s.trim());
                        for (const sel of selectors) {{
                            try {{
                                const child = el.querySelector(sel);
                                if (child) {{
                                    text = child.textContent.trim();
                                    if (text) break;
                                }}
                            }} catch(e) {{}}
                        }}
                        record[key] = text || null;
                    }});
                    return record;
                }});
            }})()
        """

        result = await connection.page.evaluate(js)
        output(result, format=format)

    run_async(_extract_records())


@app.command()
def info(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Get page information (URL, title, viewport)."""

    async def _info():
        connection = await get_connection(session_id, headless, url)

        viewport_size = connection.page.viewport_size
        info_data = {
            "url": connection.page.url,
            "title": await connection.page.title(),
            "viewport": {
                "width": viewport_size["width"] if viewport_size else None,
                "height": viewport_size["height"] if viewport_size else None,
            },
        }
        output_json(info_data)

    run_async(_info())


@app.command()
def infinite(
    extract: Optional[str] = typer.Option(None, "--extract", "-e", help="Selector to extract from each scroll"),
    max_items: int = typer.Option(100, help="Maximum items to extract"),
    scroll_delay: int = typer.Option(1000, help="Delay between scrolls (ms)"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Auto-scroll infinite scroll pages and extract data."""
    from core.progress import create_progress

    async def _infinite_scroll():
        connection = await get_connection(session_id, headless, url)
        try:
            items = []
            previous_count = 0
            no_change_count = 0

            with create_progress("Scrolling...") as progress:
                task = progress.add_task("Extracting items", total=None)

                while len(items) < max_items:
                    # Scroll to bottom
                    await connection.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await connection.page.wait_for_timeout(scroll_delay)

                    # Extract items if selector provided
                    if extract:
                        current_items = await connection.page.evaluate(f"""
                            Array.from(document.querySelectorAll('{extract}'))
                                .map(el => el.textContent?.trim() || '')
                                .filter(text => text)
                        """)
                        items = list(set(current_items))  # Remove duplicates

                    # Check if we've reached the end
                    current_count = len(items)
                    if current_count == previous_count:
                        no_change_count += 1
                        if no_change_count >= 3:
                            break
                    else:
                        no_change_count = 0

                    previous_count = current_count
                    progress.update(task, description=f"Found {len(items)} items")

                    if len(items) >= max_items:
                        break

            output_json({"items": items[:max_items], "count": len(items[:max_items])})
        except Exception as e:
            output_json({"error": str(e)})

    run_async(_infinite_scroll())


@app.command()
def paginate(
    next_selector: str = typer.Option(..., "--next", help='CSS selector of "next" button/link'),
    extract: Optional[str] = typer.Option(None, "--extract", "-e", help="Selector to extract from each page"),
    max_pages: int = typer.Option(10, help="Maximum pages to paginate"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Auto-paginate and extract data from multiple pages."""
    from core.progress import create_progress

    async def _paginate():
        connection = await get_connection(session_id, headless, url)
        try:
            all_items = []
            page = 1

            with create_progress("Paginating...") as progress:
                task = progress.add_task("Pages processed", total=max_pages)

                while page <= max_pages:
                    # Extract items from current page
                    if extract:
                        items = await connection.page.evaluate(f"""
                            Array.from(document.querySelectorAll('{extract}'))
                                .map(el => el.textContent?.trim() || '')
                                .filter(text => text)
                        """)
                        all_items.extend(items)

                    # Check if next button exists
                    next_button = connection.page.locator(next_selector).first
                    if await next_button.count() == 0:
                        break

                    # Check if next button is disabled
                    is_disabled = await next_button.evaluate('el => el.disabled || el.classList.contains("disabled")')
                    if is_disabled:
                        break

                    # Click next button
                    await next_button.click()
                    try:
                        await connection.page.wait_for_load_state("networkidle", timeout=settings.timeout)
                    except Exception as e:
                        if "Timeout" in str(e):
                            try:
                                await connection.page.wait_for_load_state("load", timeout=10000)
                            except Exception:
                                pass
                        else:
                            raise

                    page += 1
                    progress.update(task, advance=1)

            output_json({"items": all_items, "pages": page - 1, "count": len(all_items)})
        except Exception as e:
            output_json({"error": str(e)})

    run_async(_paginate())


# Valid wait_until values for Playwright
WaitUntilType = Literal["domcontentloaded", "load", "networkidle", "commit"]


async def expand_collapsible_elements(page, content_selector: str = None) -> dict:
    """Expand all collapsible elements on the page (details, accordions, FAQs, etc.).

    Args:
        page: Playwright page object
        content_selector: Optional CSS selector to limit expansion to main content area.
                         If not provided, auto-detects main/article to avoid nav elements.
    """
    result = await page.evaluate(
        """
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
    """,
        content_selector,
    )
    return result


@app.command()
def strip(
    selector: Optional[str] = typer.Option(None, help="CSS selector (default: body)"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    wait_until: str = typer.Option(
        "domcontentloaded", "--wait-until", "-w", help="Wait until: domcontentloaded, load, networkidle, commit"
    ),
    wait_for: Optional[str] = typer.Option(None, "--wait-for", help="Wait for CSS selector before extracting"),
    wait_for_text: Optional[str] = typer.Option(
        None, "--wait-for-text", help="Wait until this text appears in the page before extracting"
    ),
    settle_time: int = typer.Option(
        0, "--settle-time", help="Extra ms to wait after page load before extracting (useful for SPAs)"
    ),
    expand: bool = typer.Option(False, "--expand", "-e", help="Expand all collapsible elements before extraction"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Strip HTML and extract clean readable text."""

    async def _strip():
        connection = await get_connection(session_id, headless, url, wait_until=wait_until)
        if wait_for:
            await connection.page.wait_for_selector(wait_for, timeout=settings.timeout)
        if wait_for_text:
            await connection.page.wait_for_function(
                f"document.body.innerText.includes({json.dumps(wait_for_text)})",
                timeout=settings.timeout,
            )
        if settle_time > 0:
            await connection.page.wait_for_timeout(settle_time)
        try:
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
            output_json({"error": str(e)})

    run_async(_strip())


@app.command()
def markdown(
    selector: Optional[str] = typer.Option(None, help="CSS selector (default: body)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    wait_until: str = typer.Option(
        "domcontentloaded", "--wait-until", "-w", help="Wait until: domcontentloaded, load, networkidle, commit"
    ),
    wait_for: Optional[str] = typer.Option(None, "--wait-for", help="Wait for CSS selector before extracting"),
    wait_for_text: Optional[str] = typer.Option(
        None, "--wait-for-text", help="Wait until this text appears in the page before extracting"
    ),
    settle_time: int = typer.Option(
        0, "--settle-time", help="Extra ms to wait after page load before extracting (useful for SPAs)"
    ),
    expand: bool = typer.Option(False, "--expand", "-e", help="Expand all collapsible elements before extraction"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Convert page or element to Markdown."""
    import markdownify

    async def _markdown():
        connection = await get_connection(session_id, headless, url, wait_until=wait_until)
        if wait_for:
            await connection.page.wait_for_selector(wait_for, timeout=settings.timeout)
        if wait_for_text:
            await connection.page.wait_for_function(
                f"document.body.innerText.includes({json.dumps(wait_for_text)})",
                timeout=settings.timeout,
            )
        if settle_time > 0:
            await connection.page.wait_for_timeout(settle_time)
        try:
            # Expand collapsible elements if requested
            if expand:
                await expand_collapsible_elements(connection.page)
                await connection.page.wait_for_timeout(500)  # Brief wait for animations

            if selector:
                html = await connection.page.locator(selector).first.inner_html()
            else:
                html = await connection.page.content()

            md = markdownify.markdownify(html, heading_style="ATX")

            if output:
                with open(output, "w", encoding="utf-8") as f:
                    f.write(md)
                output_json({"message": f"Markdown saved to {output}"})
            else:
                if not settings.quiet:
                    print(md)
        except Exception as e:
            output_json({"error": str(e)})

    run_async(_markdown())


@app.command()
def meta(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Extract meta tags (title, description, og:*, twitter:*)."""

    async def _meta():
        connection = await get_connection(session_id, headless, url)
        try:
            meta_data = await connection.page.evaluate("""
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
            """)

            output_json(meta_data)
        except Exception as e:
            output_json({"error": str(e)})

    run_async(_meta())


@app.command()
def schema(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Extract structured data (JSON-LD, microdata, RDFa)."""

    async def _schema():
        connection = await get_connection(session_id, headless, url)
        try:
            schemas = await connection.page.evaluate("""
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
            """)

            output_json(schemas)
        except Exception as e:
            output_json({"error": str(e)})

    run_async(_schema())


@app.command()
def xpath(
    xpath: str = typer.Argument(..., help="XPath expression"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    attribute: Optional[str] = typer.Option(None, help="Extract attribute value"),
    text: bool = typer.Option(False, "--text/--html", help="Extract text content (default: HTML)"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Query elements by XPath."""

    async def _xpath():
        connection = await get_connection(session_id, headless, url)
        try:
            # Build JavaScript function with parameters embedded
            js_code = f"""
                (() => {{
                    const xpath = {json.dumps(xpath)};
                    const attribute = {json.dumps(attribute or "")};
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
            """
            results = await connection.page.evaluate(js_code)

            if len(results) == 1:
                output_json({"result": results[0]})
            else:
                output_json({"results": results})
        except Exception as e:
            output_json({"error": str(e)})

    run_async(_xpath())


@app.command()
def regex(
    pattern: str = typer.Argument(..., help="Regex pattern"),
    selector: Optional[str] = typer.Option(None, help="CSS selector (default: body)"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Extract text matching regex pattern."""

    async def _regex():
        connection = await get_connection(session_id, headless, url)
        try:
            if selector:
                text = await connection.page.locator(selector).first.text_content()
            else:
                text = await connection.page.evaluate("document.body.textContent")

            matches = re.findall(pattern, text or "", re.MULTILINE | re.DOTALL)

            if len(matches) == 1:
                output_json({"match": matches[0]})
            else:
                output_json({"matches": matches})
        except Exception as e:
            output_json({"error": str(e)})

    run_async(_regex())


@app.command()
def forms(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    wait_for: Optional[str] = typer.Option(None, "--wait-for", help="Wait for CSS selector before extracting"),
    wait_for_text: Optional[str] = typer.Option(
        None, "--wait-for-text", help="Wait until this text appears in the page before extracting"
    ),
    settle_time: int = typer.Option(
        0, "--settle-time", help="Extra ms to wait after page load before extracting (useful for SPAs)"
    ),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """List all forms with their fields and actions."""

    async def _forms():
        connection = await get_connection(session_id, headless, url)
        if wait_for:
            await connection.page.wait_for_selector(wait_for, timeout=settings.timeout)
        if wait_for_text:
            await connection.page.wait_for_function(
                f"document.body.innerText.includes({json.dumps(wait_for_text)})",
                timeout=settings.timeout,
            )
        if settle_time > 0:
            await connection.page.wait_for_timeout(settle_time)
        try:
            forms_data = await connection.page.evaluate("""
                () => {
                    const forms = [];
                    let index = 0;

                    function extractFieldData(field) {
                        const fd = {
                            type: field.type || field.tagName.toLowerCase(),
                            name: field.name || null,
                            id: field.id || null,
                            placeholder: field.placeholder || null,
                            required: field.required || false,
                            value: field.value || null
                        };
                        if (field.tagName === 'SELECT') {
                            fd.options = Array.from(field.options).map(opt => ({
                                value: opt.value,
                                text: opt.text
                            }));
                        }
                        return fd;
                    }

                    function extractFields(container) {
                        const fields = [];
                        container.querySelectorAll('input, textarea, select').forEach(field => {
                            fields.push(extractFieldData(field));
                        });
                        return fields;
                    }

                    // Phase A: Standard <form> elements
                    document.querySelectorAll('form').forEach((form) => {
                        forms.push({
                            index: index++,
                            id: form.id || null,
                            name: form.name || null,
                            action: form.action || null,
                            method: form.method || 'get',
                            type: 'form',
                            fields: extractFields(form)
                        });
                    });

                    // Phase B: Elements with role="form" not inside a <form>
                    document.querySelectorAll('[role="form"]').forEach((el) => {
                        if (el.tagName.toLowerCase() === 'form') return;
                        if (el.closest('form')) return;
                        forms.push({
                            index: index++,
                            id: el.id || null,
                            name: el.getAttribute('aria-label') || el.getAttribute('name') || null,
                            action: null,
                            method: null,
                            type: 'role-form',
                            selector: el.tagName.toLowerCase() + (el.id ? '#' + el.id : ''),
                            fields: extractFields(el)
                        });
                    });

                    // Phase C: Orphan inputs not inside any form or role="form" container
                    const orphanInputs = Array.from(
                        document.querySelectorAll('input, textarea, select')
                    ).filter(el => !el.closest('form') && !el.closest('[role="form"]'));

                    if (orphanInputs.length > 0) {
                        // Walk up from each input to find the lowest ancestor that:
                        // 1. Contains multiple orphan inputs (logical group), OR
                        // 2. Is a semantic/named element (custom element, has id/aria-label, or non-div/span)
                        // This handles SPAs where inputs sit inside custom elements like <shreddit-search>.
                        function getGroupContainer(field, allOrphans) {
                            let node = field.parentElement;
                            while (node && node !== document.body && node !== document.documentElement) {
                                const tag = node.tagName.toLowerCase();
                                // Named container: has id, aria-label, or role
                                if (node.id || node.getAttribute('aria-label') || node.getAttribute('role')) return node;
                                // Semantic container: not a generic div/span (e.g. custom element, section, fieldset)
                                if (tag !== 'div' && tag !== 'span') return node;
                                // Shared container: this ancestor contains more than one orphan input
                                if (allOrphans.filter(f => node.contains(f)).length > 1) return node;
                                node = node.parentElement;
                            }
                            return field.parentElement || field;
                        }

                        const containers = new Map();
                        orphanInputs.forEach(field => {
                            const container = getGroupContainer(field, orphanInputs);
                            if (!containers.has(container)) containers.set(container, new Set());
                            containers.get(container).add(field);
                        });
                        containers.forEach((fieldSet, container) => {
                            const tagName = container.tagName.toLowerCase();
                            const selector = tagName + (container.id ? '#' + container.id : (container.className ? '.' + container.className.trim().split(/ +/)[0] : ''));
                            forms.push({
                                index: index++,
                                id: container.id || null,
                                name: container.getAttribute('aria-label') || container.getAttribute('name') || null,
                                action: null,
                                method: null,
                                type: 'implicit',
                                selector: selector,
                                fields: Array.from(fieldSet).map(extractFieldData)
                            });
                        });
                    }

                    return forms;
                }
            """)

            output_json({"forms": forms_data})
        except Exception as e:
            output_json({"error": str(e)})

    run_async(_forms())


@app.command()
def expand(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    wait_until: str = typer.Option(
        "networkidle", "--wait-until", "-w", help="Wait until: domcontentloaded, load, networkidle, commit"
    ),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Expand all collapsible elements on the page (details, accordions, FAQs, etc.)."""

    async def _expand():
        connection = await get_connection(session_id, headless, url, wait_until=wait_until)
        try:
            result = await expand_collapsible_elements(connection.page)
            await connection.page.wait_for_timeout(500)  # Brief wait for animations

            output_json(
                {
                    "message": f"Expanded {result['expanded']} collapsible elements",
                    "expanded_count": result["expanded"],
                    "errors": result.get("errors", []),
                }
            )
        except Exception as e:
            output_json({"error": str(e)})

    run_async(_expand())


@app.command()
def smart(
    url: str = typer.Argument(..., help="URL to scrape"),
    selector: Optional[str] = typer.Option(
        None, "--selector", "-s", help="CSS selector for main content (auto-detected if not provided)"
    ),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option("text", "--format", "-f", help="Output format: text, markdown, html, json"),
    no_expand: bool = typer.Option(False, "--no-expand", help="Skip expanding collapsible elements"),
    wait_timeout: int = typer.Option(3000, "--wait-timeout", help="Additional wait time after page load (ms)"),
    wait_for: Optional[str] = typer.Option(
        None, "--wait-for", help="CSS selector to wait for before extraction (for SPA routes)"
    ),
    wait_for_text: Optional[str] = typer.Option(
        None, "--wait-for-text", help="Text content to wait for before extraction"
    ),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Smart scrape: handles SPAs, expands content, extracts clean text.

    Designed for modern JavaScript-heavy sites (React, Next.js, Vue, etc.)
    that require special handling for dynamic content.

    Use --wait-for to specify a CSS selector that must appear before extraction.
    Use --wait-for-text to wait for specific text content to appear on the page.
    """
    import html2text
    import markdownify

    async def _smart():
        connection = await get_connection(session_id, headless, url, wait_until="load")
        try:
            # Step 1b: Wait for specific selector if provided (for SPA routes)
            if wait_for:
                await connection.page.wait_for_selector(wait_for, timeout=settings.timeout)

            # Step 1c: Wait for specific text if provided
            if wait_for_text:
                await connection.page.wait_for_function(
                    f"document.body.innerText.includes({json.dumps(wait_for_text)})", timeout=settings.timeout
                )

            # Step 2: Additional wait for any lazy-loaded content
            await connection.page.wait_for_timeout(wait_timeout)

            # Step 3: Expand collapsible elements (unless disabled)
            expanded_count = 0
            if not no_expand:
                result = await expand_collapsible_elements(connection.page)
                expanded_count = result.get("expanded", 0)
                if expanded_count > 0:
                    await connection.page.wait_for_timeout(1000)  # Wait for expanded content

            # Step 4: Auto-detect main content selector if not provided
            content_selector = selector
            if not content_selector:
                content_selector = await connection.page.evaluate("""
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
                """)

            # Step 5: Extract content
            if content_selector == "body":
                html_content = await connection.page.content()
            else:
                try:
                    html_content = await connection.page.locator(content_selector).first.inner_html()
                except Exception:
                    html_content = await connection.page.content()

            # Step 6: Get page metadata
            title = await connection.page.title()
            page_url = connection.page.url

            # Step 7: Format output
            if format == "html":
                final_content = html_content
            elif format == "markdown":
                final_content = markdownify.markdownify(html_content, heading_style="ATX")
            elif format == "json":
                h = html2text.HTML2Text()
                h.ignore_links = False
                h.ignore_images = False
                h.body_width = 0
                text_content = h.handle(html_content).strip()

                json_output = {
                    "url": page_url,
                    "title": title,
                    "selector_used": content_selector,
                    "expanded_elements": expanded_count,
                    "content": text_content,
                    "content_length": len(text_content),
                    "word_count": len(text_content.split()),
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
                with open(output, "w", encoding="utf-8") as f:
                    f.write(final_content)
                output_json(
                    {
                        "message": f"Content saved to {output}",
                        "url": page_url,
                        "title": title,
                        "selector_used": content_selector,
                        "expanded_elements": expanded_count,
                        "format": format,
                        "content_length": len(final_content),
                        "word_count": len(final_content.split()) if format in ["text", "markdown"] else None,
                    }
                )
            else:
                if not settings.quiet:
                    print(final_content)

        except Exception as e:
            output_json({"error": str(e)})

    run_async(_smart())


# ---------------------------------------------------------------------------
# Accessibility-tree helpers for smart-records
# ---------------------------------------------------------------------------


def _find_nodes_by_role(tree: Dict[str, Any], role: str) -> List[Dict[str, Any]]:
    """Recursively find all nodes whose role matches (case-insensitive)."""
    results: List[Dict[str, Any]] = []
    if not tree:
        return results
    if tree.get("role", "").lower() == role.lower():
        results.append(tree)
    for child in tree.get("children", []) or []:
        results.extend(_find_nodes_by_role(child, role))
    return results


def _flatten_node(node: Dict[str, Any]) -> List[tuple]:
    """DFS-flatten a node's subtree into (role, name, value) tuples."""
    items: List[tuple] = []
    role = node.get("role", "")
    name = node.get("name", "") or ""
    value = node.get("value", "") or ""
    items.append((role, name, value))
    for child in node.get("children", []) or []:
        items.extend(_flatten_node(child))
    return items


_DATE_RE = re.compile(
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b"
    r"|\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b"
    r"|\b\d{4}-\d{2}-\d{2}\b"
    r"|\bon\s+[A-Z][a-z]+\s+\d{1,2},?\s+\d{4}\b",
    re.IGNORECASE,
)
_STARS_RE = re.compile(r"\b\d[\d,]*(?:\.\d+)?k?\b", re.IGNORECASE)


def _extract_fields_from_node(node: Dict[str, Any], fields: Optional[List[str]]) -> Dict[str, Any]:
    """Extract fields from an accessibility node using heuristics."""
    flat = _flatten_node(node)

    def _text(item: tuple) -> str:
        _, name, value = item
        return (name or value or "").strip()

    record: Dict[str, Any] = {}

    wanted = set(fields) if fields else None

    # --- name/title ---
    if wanted is None or "name" in wanted or "title" in wanted:
        for role, name, value in flat:
            if role.lower() == "heading" and name.strip():
                key = "name" if (wanted is None or "name" in wanted) else "title"
                record[key] = name.strip()
                break

    # --- url/link ---
    if wanted is None or "url" in wanted or "link" in wanted:
        for role, name, value in flat:
            if role.lower() == "link":
                link_val = value.strip() if value else name.strip()
                key = "url" if (wanted is None or "url" in wanted) else "link"
                record[key] = link_val or None
                break

    # --- stars ---
    if wanted is None or "stars" in wanted:
        for role, name, value in flat:
            txt = _text((role, name, value))
            if "star" in txt.lower() or ("k" in txt.lower() and _STARS_RE.search(txt)):
                record["stars"] = txt or None
                break

    # --- language ---
    if wanted is None or "language" in wanted:
        for role, name, value in flat:
            txt = _text((role, name, value))
            if "language" in (name or "").lower():
                record["language"] = txt or None
                break

    # --- updated ---
    if wanted is None or "updated" in wanted:
        for role, name, value in flat:
            txt = _text((role, name, value))
            if _DATE_RE.search(txt):
                record["updated"] = txt or None
                break

    # --- description ---
    if wanted is None or "description" in wanted:
        candidates = []
        for role, name, value in flat:
            if role.lower() in ("generic", "statictext", "paragraph", "text") and name.strip():
                # Skip things already captured
                if name.strip() not in record.values():
                    candidates.append(name.strip())
        if candidates:
            record["description"] = max(candidates, key=len)

    # Fill None for explicitly requested fields not found
    if fields:
        for f in fields:
            if f not in record:
                record[f] = None

    return record


@app.command("smart-records")
def smart_records(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to (uses current page if omitted)"),
    container: str = typer.Option(
        "article", "--container", "-c", help="ARIA role or tag to group repeating elements by"
    ),
    fields: Optional[str] = typer.Option(
        None,
        "--fields",
        "-f",
        help="Comma-separated field names to extract (e.g. name,description,stars). Extracts all if omitted.",
    ),
    limit: int = typer.Option(0, "--limit", "-l", help="Max records to return (0 = all)"),
    format: Optional[str] = typer.Option(None, "--format", help="Output format: json, plain, table, csv"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(
        None, "--headless/--headed", help="Run in headless mode (overrides global)"
    ),
):
    """Extract structured records from repeating semantic elements via accessibility tree.

    Uses Playwright's accessibility snapshot instead of CSS selectors — ideal for SPAs
    with auto-generated class names (GitHub, React apps, etc.).

    Examples:
        cli.py extract smart-records --url "https://github.com/trending" --container article --fields "name,description,language,stars"
        cli.py extract smart-records --url "https://news.ycombinator.com" --container listitem --limit 20
    """

    field_list: Optional[List[str]] = [f.strip() for f in fields.split(",")] if fields else None

    async def _smart_records():
        connection = await get_connection(session_id, headless, None)

        if url:
            try:
                await connection.page.goto(url, wait_until="networkidle", timeout=30000)
            except Exception:
                try:
                    await connection.page.goto(url, wait_until="load", timeout=30000)
                except Exception as e:
                    output_json({"error": f"Failed to navigate to {url}: {e}"})
                    return

        snapshot = await connection.page.accessibility.snapshot()
        if not snapshot:
            output_json({"error": "Accessibility snapshot returned None. Page may not have loaded."})
            return

        # Try container role first; fall back to common alternatives
        nodes = _find_nodes_by_role(snapshot, container)
        if not nodes and container.lower() == "article":
            nodes = _find_nodes_by_role(snapshot, "listitem")
        if not nodes and container.lower() in ("article", "listitem"):
            nodes = _find_nodes_by_role(snapshot, "row")

        if not nodes:
            output_json({"error": f"No nodes with role '{container}' found in accessibility tree.", "records": []})
            return

        if limit > 0:
            nodes = nodes[:limit]

        records_out = [_extract_fields_from_node(n, field_list) for n in nodes]
        output_json(records_out)

    run_async(_smart_records())
