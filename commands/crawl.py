"""Web crawling commands."""

import asyncio
import json
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse

import typer

from core.async_command import get_connection, run_async
from core.browser import get_browser_manager
from core.output import output_json
from core.progress import create_progress, log_verbose
from core.settings import settings

app = typer.Typer()


def is_valid_url(url: str, base_domain: str) -> bool:
    """Check if URL is valid and belongs to base domain."""
    try:
        parsed = urlparse(url)
        base_parsed = urlparse(base_domain)
        return parsed.netloc == base_parsed.netloc or parsed.netloc == ""
    except Exception:
        return False


@app.command()
def site(
    url: str,
    depth: int = typer.Option(2, "--depth", "-d", help="Maximum crawl depth"),
    extract: Optional[str] = typer.Option(None, "--extract", "-e", help="Selector to extract from each page"),
    follow: Optional[str] = typer.Option(None, help="URL pattern to follow (glob pattern)"),
    exclude: Optional[str] = typer.Option(None, help="URL pattern to exclude (glob pattern)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output directory for results"),
    concurrency: int = typer.Option(1, "--concurrency", "-c", help="Number of parallel requests [default: 1]"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Crawl a website following links."""
    import fnmatch
    import os

    async def _crawl():
        visited: Set[str] = set()
        to_visit: List[tuple[str, int]] = [(url, 0)]  # (url, depth)
        results = []
        base_domain = urlparse(url).netloc

        # Create output directory if specified
        if output:
            os.makedirs(output, exist_ok=True)

        # Slot pool: max `concurrency` browser instances, reused across all pages
        slot_pool: asyncio.Queue = asyncio.Queue()
        for i in range(concurrency):
            await slot_pool.put(i)

        async def crawl_page(page_url: str, current_depth: int):
            """Crawl a single page."""
            if page_url in visited or current_depth > depth:
                return None

            visited.add(page_url)
            log_verbose(f"Crawling {page_url} (depth {current_depth})")

            # Borrow a slot from the pool (limits to `concurrency` browsers)
            slot = await slot_pool.get()
            try:
                connection = await get_connection(f"{session_id or 'crawl'}-{slot}", headless, page_url)

                result = {
                    "url": page_url,
                    "depth": current_depth,
                    "title": await connection.page.title(),
                }

                # Extract data if selector provided
                if extract:
                    try:
                        extracted = await connection.page.evaluate(f"""
                            Array.from(document.querySelectorAll('{extract}'))
                                .map(el => el.textContent?.trim() || '')
                                .filter(text => text)
                        """)
                        result["extracted"] = extracted if len(extracted) > 1 else (extracted[0] if extracted else "")
                    except Exception as e:
                        result["extract_error"] = str(e)

                # Extract links for next level
                if current_depth < depth:
                    links = await connection.page.evaluate("""
                        Array.from(document.querySelectorAll('a'))
                            .map(a => a.href)
                            .filter(href => href && !href.startsWith('javascript:') && !href.startsWith('mailto:'))
                    """)

                    # Filter and add new URLs
                    for link in links:
                        # Make absolute URL
                        absolute_url = urljoin(page_url, link)
                        parsed = urlparse(absolute_url)

                        # Check if URL matches follow pattern
                        if follow and not fnmatch.fnmatch(absolute_url, follow):
                            continue

                        # Check if URL matches exclude pattern
                        if exclude and fnmatch.fnmatch(absolute_url, exclude):
                            continue

                        # Check if same domain
                        if parsed.netloc == base_domain or parsed.netloc == "":
                            if absolute_url not in visited:
                                to_visit.append((absolute_url, current_depth + 1))

                # Save to file if output directory specified
                if output:
                    safe_filename = urlparse(page_url).path.replace("/", "_") or "index"
                    if safe_filename.startswith("_"):
                        safe_filename = safe_filename[1:]
                    if not safe_filename:
                        safe_filename = "index"
                    output_file = os.path.join(output, f"{safe_filename}.json")
                    with open(output_file, "w") as f:
                        json.dump(result, f, indent=2)

                return result
            finally:
                await slot_pool.put(slot)

        # The slot_pool already limits concurrency — no separate semaphore needed
        with create_progress("Crawling site...") as progress:
            task = progress.add_task("Pages crawled", total=None)

            while to_visit:
                # Dispatch a batch of pending URLs concurrently (pool enforces limit)
                batch = []
                while to_visit:
                    url_item = to_visit.pop(0)
                    if url_item[0] not in visited:
                        batch.append(url_item)

                if not batch:
                    break

                tasks = [crawl_page(url_item[0], url_item[1]) for url_item in batch]
                for coro in asyncio.as_completed(tasks):
                    result = await coro
                    if result:
                        results.append(result)
                    progress.update(task, advance=1)

        output_json(
            {
                "total_pages": len(results),
                "results": results,
            }
        )

    run_async(_crawl())


@app.command()
def sitemap(
    url: str,
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Parse sitemap.xml and return URLs."""
    import xml.etree.ElementTree as ET

    async def _sitemap():
        connection = await get_connection(session_id, headless)

        # Try common sitemap locations
        sitemap_urls = [
            url if url.endswith(".xml") else f"{url}/sitemap.xml",
            f"{url}/sitemap_index.xml",
            f"{url}/sitemap-index.xml",
        ]

        sitemap_content = None
        found_url = None

        for sitemap_url in sitemap_urls:
            try:
                response = await connection.page.request.get(sitemap_url)
                if response.status == 200:
                    sitemap_content = await response.text()
                    found_url = sitemap_url
                    break
            except Exception:
                continue

        if not sitemap_content:
            output_json({"error": "Sitemap not found"})
            return

        # Parse XML
        try:
            root = ET.fromstring(sitemap_content)

            # Handle namespace
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

            urls = []

            # Check if it's a sitemap index
            sitemaps = root.findall(".//sm:sitemap/sm:loc", ns)
            if sitemaps:
                # It's a sitemap index
                for sitemap in sitemaps:
                    urls.append({"type": "sitemap", "url": sitemap.text})
            else:
                # It's a regular sitemap
                url_elements = root.findall(".//sm:url", ns)
                for url_elem in url_elements:
                    loc = url_elem.find("sm:loc", ns)
                    lastmod = url_elem.find("sm:lastmod", ns)
                    changefreq = url_elem.find("sm:changefreq", ns)
                    priority = url_elem.find("sm:priority", ns)

                    urls.append(
                        {
                            "type": "url",
                            "url": loc.text if loc is not None else None,
                            "lastmod": lastmod.text if lastmod is not None else None,
                            "changefreq": changefreq.text if changefreq is not None else None,
                            "priority": priority.text if priority is not None else None,
                        }
                    )

            output_json({"sitemap_url": found_url, "total_urls": len(urls), "urls": urls})
        except Exception as e:
            output_json({"error": f"Failed to parse sitemap: {str(e)}"})

    run_async(_sitemap())


@app.command()
def rss(
    url: str,
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Parse RSS/Atom feed."""
    import xml.etree.ElementTree as ET

    async def _rss():
        connection = await get_connection(session_id, headless)

        try:
            response = await connection.page.request.get(url)
            if response.status != 200:
                output_json({"error": f"Failed to fetch feed: HTTP {response.status}"})
                return

            feed_content = await response.text()
            root = ET.fromstring(feed_content)

            items = []

            # Check if it's RSS or Atom
            if root.tag == "rss" or root.find("channel") is not None:
                # RSS feed
                channel = root.find("channel")
                feed_info = {
                    "type": "rss",
                    "title": channel.find("title").text if channel.find("title") is not None else None,
                    "link": channel.find("link").text if channel.find("link") is not None else None,
                    "description": channel.find("description").text
                    if channel.find("description") is not None
                    else None,
                }

                for item in channel.findall("item"):
                    items.append(
                        {
                            "title": item.find("title").text if item.find("title") is not None else None,
                            "link": item.find("link").text if item.find("link") is not None else None,
                            "description": item.find("description").text
                            if item.find("description") is not None
                            else None,
                            "pubDate": item.find("pubDate").text if item.find("pubDate") is not None else None,
                            "guid": item.find("guid").text if item.find("guid") is not None else None,
                        }
                    )
            else:
                # Atom feed
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                feed_info = {
                    "type": "atom",
                    "title": root.find("atom:title", ns).text if root.find("atom:title", ns) is not None else None,
                    "link": root.find("atom:link", ns).get("href") if root.find("atom:link", ns) is not None else None,
                }

                for entry in root.findall("atom:entry", ns):
                    items.append(
                        {
                            "title": entry.find("atom:title", ns).text
                            if entry.find("atom:title", ns) is not None
                            else None,
                            "link": entry.find("atom:link", ns).get("href")
                            if entry.find("atom:link", ns) is not None
                            else None,
                            "summary": entry.find("atom:summary", ns).text
                            if entry.find("atom:summary", ns) is not None
                            else None,
                            "published": entry.find("atom:published", ns).text
                            if entry.find("atom:published", ns) is not None
                            else None,
                            "id": entry.find("atom:id", ns).text if entry.find("atom:id", ns) is not None else None,
                        }
                    )

            output_json({"feed": feed_info, "total_items": len(items), "items": items})
        except Exception as e:
            output_json({"error": f"Failed to parse feed: {str(e)}"})

    run_async(_rss())
