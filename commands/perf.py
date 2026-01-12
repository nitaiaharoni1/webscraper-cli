"""Performance analysis commands."""

import typer
import json
from typing import Optional
from core.browser import get_or_create_connection
from core.settings import settings

app = typer.Typer()


def output_result(data):
    """Output data in the configured format."""
    if settings.format == 'json':
        print(json.dumps(data, indent=2))
    else:
        print(data)


@app.command()
def vitals(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Get Core Web Vitals (LCP, FID, CLS, TTFB)."""
    import asyncio

    async def _vitals():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        if url:
            await connection.page.goto(url, wait_until='networkidle')
        
        # Get performance metrics
        metrics = await connection.page.evaluate('''
            () => {
                const timing = performance.timing;
                const navigation = performance.getEntriesByType('navigation')[0];
                
                // Calculate metrics
                const ttfb = timing.responseStart - timing.requestStart;
                const domContentLoaded = timing.domContentLoadedEventEnd - timing.navigationStart;
                const loadComplete = timing.loadEventEnd - timing.navigationStart;
                
                // Try to get paint metrics
                const paintEntries = performance.getEntriesByType('paint');
                const fcp = paintEntries.find(e => e.name === 'first-contentful-paint');
                const lcp = performance.getEntriesByType('largest-contentful-paint').slice(-1)[0];
                
                return {
                    ttfb: ttfb,
                    fcp: fcp ? fcp.startTime : null,
                    lcp: lcp ? lcp.renderTime || lcp.loadTime : null,
                    domContentLoaded: domContentLoaded,
                    loadComplete: loadComplete,
                    transferSize: navigation ? navigation.transferSize : null,
                    domInteractive: timing.domInteractive - timing.navigationStart
                };
            }
        ''')
        
        output_result({
            'core_web_vitals': metrics,
            'url': connection.page.url
        })

    asyncio.run(_vitals())


@app.command()
def lighthouse(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Run basic performance audit (simplified lighthouse-style metrics)."""
    import asyncio

    async def _lighthouse():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        if url:
            await connection.page.goto(url, wait_until='networkidle')
        
        # Collect various metrics
        audit = await connection.page.evaluate('''
            () => {
                const timing = performance.timing;
                const resources = performance.getEntriesByType('resource');
                
                // Count resources by type
                const resourceCounts = {};
                const resourceSizes = {};
                resources.forEach(r => {
                    const type = r.initiatorType || 'other';
                    resourceCounts[type] = (resourceCounts[type] || 0) + 1;
                    resourceSizes[type] = (resourceSizes[type] || 0) + (r.transferSize || 0);
                });
                
                // Check for common issues
                const images = Array.from(document.images);
                const imagesWithoutAlt = images.filter(img => !img.alt).length;
                
                const links = Array.from(document.links);
                const httpsLinks = links.filter(a => a.href.startsWith('https://')).length;
                
                return {
                    performance: {
                        loadTime: timing.loadEventEnd - timing.navigationStart,
                        domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
                        ttfb: timing.responseStart - timing.requestStart
                    },
                    resources: {
                        counts: resourceCounts,
                        sizes: resourceSizes,
                        total: resources.length
                    },
                    accessibility: {
                        totalImages: images.length,
                        imagesWithoutAlt: imagesWithoutAlt
                    },
                    security: {
                        totalLinks: links.length,
                        httpsLinks: httpsLinks,
                        httpLinks: links.length - httpsLinks
                    },
                    dom: {
                        nodeCount: document.getElementsByTagName('*').length
                    }
                };
            }
        ''')
        
        # Calculate scores (simplified)
        perf_score = 100
        if audit['performance']['loadTime'] > 3000:
            perf_score -= 30
        if audit['performance']['ttfb'] > 600:
            perf_score -= 20
        
        a11y_score = 100
        if audit['accessibility']['imagesWithoutAlt'] > 0:
            ratio = audit['accessibility']['imagesWithoutAlt'] / max(audit['accessibility']['totalImages'], 1)
            a11y_score -= int(ratio * 50)
        
        output_result({
            'scores': {
                'performance': max(0, perf_score),
                'accessibility': max(0, a11y_score)
            },
            'audit': audit,
            'url': connection.page.url
        })

    asyncio.run(_lighthouse())


@app.command()
def memory(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Get JavaScript heap usage and DOM node counts."""
    import asyncio

    async def _memory():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        if url:
            await connection.page.goto(url, wait_until='networkidle')
        
        # Get memory metrics
        memory_info = await connection.page.evaluate('''
            () => {
                const mem = performance.memory || {};
                const nodes = document.getElementsByTagName('*').length;
                
                // getEventListeners is only available in Chrome DevTools console, not in regular JS
                // We'll skip it or try to count manually if possible
                let eventListeners = 'unavailable';
                try {
                    if (typeof getEventListeners !== 'undefined') {
                        eventListeners = Object.keys(getEventListeners(document)).length;
                    }
                } catch (e) {
                    // getEventListeners not available
                }
                
                return {
                    jsHeapSizeLimit: mem.jsHeapSizeLimit,
                    totalJSHeapSize: mem.totalJSHeapSize,
                    usedJSHeapSize: mem.usedJSHeapSize,
                    domNodes: nodes,
                    eventListeners: eventListeners
                };
            }
        ''')
        
        # Format sizes
        if memory_info.get('jsHeapSizeLimit'):
            memory_info['jsHeapSizeLimitMB'] = round(memory_info['jsHeapSizeLimit'] / (1024 * 1024), 2)
            memory_info['totalJSHeapSizeMB'] = round(memory_info['totalJSHeapSize'] / (1024 * 1024), 2)
            memory_info['usedJSHeapSizeMB'] = round(memory_info['usedJSHeapSize'] / (1024 * 1024), 2)
            memory_info['heapUsagePercent'] = round((memory_info['usedJSHeapSize'] / memory_info['jsHeapSizeLimit']) * 100, 2)
        
        output_result({
            'memory': memory_info,
            'url': connection.page.url
        })

    asyncio.run(_memory())
