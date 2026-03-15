"""Reconnaissance command — one-shot page analysis."""

import json
from typing import Optional

import typer

from core.async_command import get_connection, run_async
from core.output import output_json
from core.settings import settings

app = typer.Typer()

# Common semantic selectors to probe for presence on the page
_KEY_SELECTOR_PROBES = [
    "h1",
    "h2",
    "h3",
    "p",
    "table",
    "form",
    "input",
    "button",
    "nav",
    "main",
    "article",
    "section",
    "aside",
    "footer",
    ".content",
    "#content",
    "#main",
    "[role='main']",
    ".container",
    "ul li",
    "ol li",
    ".card",
    ".item",
    ".row",
]

_RECON_JS = """
    () => {
        // Headings
        const headings = Array.from(document.querySelectorAll('h1, h2, h3')).slice(0, 20).map(h => ({
            tag: h.tagName,
            text: h.textContent.trim().slice(0, 120)
        }));

        // Forms summary
        const forms = Array.from(document.querySelectorAll('form, [role="form"]')).map((f, i) => {
            const fields = Array.from(f.querySelectorAll('input, textarea, select'));
            const tag = f.tagName.toLowerCase();
            const id = f.id ? '#' + f.id : '';
            const cls = f.className ? '.' + f.className.trim().split(/\\s+/)[0] : '';
            return {
                index: i,
                selector: tag + (id || cls),
                action: f.action || null,
                method: (f.method || 'get').toUpperCase(),
                field_count: fields.length,
                field_names: fields.slice(0, 8).map(el => el.name || el.id || el.placeholder || el.type).filter(Boolean)
            };
        });

        // Tables summary
        const tables = Array.from(document.querySelectorAll('table')).map((t, i) => {
            const rows = t.querySelectorAll('tr').length;
            const cols = t.querySelector('tr') ? t.querySelector('tr').querySelectorAll('th, td').length : 0;
            const tag = t.tagName.toLowerCase();
            const cls = t.className ? '.' + t.className.trim().split(/\\s+/)[0] : '';
            return { index: i, selector: tag + cls, rows, cols };
        });

        // Links
        const allLinks = Array.from(document.querySelectorAll('a[href]'));
        const origin = location.origin;
        const internalLinks = allLinks.filter(a => a.href.startsWith(origin)).length;
        const externalLinks = allLinks.filter(a => !a.href.startsWith(origin) && !a.href.startsWith('javascript:')).length;

        // Images
        const imgs = document.querySelectorAll('img');
        const missingAlt = Array.from(imgs).filter(i => !i.alt).length;

        // SPA detection heuristics
        const spaIndicators = !!(
            document.querySelector('#root, #app, #__next, [data-reactroot], [ng-app], [data-v-app]') ||
            (window.__NEXT_DATA__ !== undefined) ||
            (window.__nuxt !== undefined) ||
            document.querySelector('script[src*="react"], script[src*="vue"], script[src*="angular"]')
        );

        // Page type guess
        let pageType = 'static';
        if (spaIndicators) pageType = 'spa';
        else if (forms.length > 0 && allLinks.length < 10) pageType = 'form';
        else if (tables.length > 0) pageType = 'data';

        return {
            url: location.href,
            title: document.title,
            page_type: pageType,
            spa_indicators: spaIndicators,
            headings,
            forms,
            tables,
            links: { total: allLinks.length, internal: internalLinks, external: externalLinks },
            images: { total: imgs.length, missing_alt: missingAlt }
        };
    }
"""


@app.command()
def recon(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to first"),
    selectors: bool = typer.Option(True, "--selectors/--no-selectors", help="Include key_selectors probe"),
    wait_for: Optional[str] = typer.Option(None, "--wait-for", help="Wait for CSS selector before analysis"),
    settle_time: int = typer.Option(0, "--settle-time", help="Extra ms to wait after page load (useful for SPAs)"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """One-shot page reconnaissance: headings, forms, tables, links, images, SPA detection.

    Replaces the 4-command manual recon workflow with a single call. Returns a complete
    structural overview of the page — ideal as the first step of any automation task.

    Examples:
        cli.py recon --url https://example.com
        cli.py recon --url https://news.ycombinator.com --no-selectors
        cli.py goto https://example.com && cli.py recon
    """

    async def _recon():
        connection = await get_connection(session_id, headless, url)

        if wait_for:
            await connection.page.wait_for_selector(wait_for, timeout=settings.timeout)
        if settle_time > 0:
            await connection.page.wait_for_timeout(settle_time)

        result = await connection.page.evaluate(_RECON_JS)

        if selectors:
            # Probe which common selectors match at least one element
            matched = []
            for probe in _KEY_SELECTOR_PROBES:
                probe_json = json.dumps(probe)
                count = await connection.page.evaluate(f"() => document.querySelectorAll({probe_json}).length")
                if count > 0:
                    matched.append({"selector": probe, "count": count})
            result["key_selectors"] = matched

        output_json(result)

    run_async(_recon())
