"""Audit commands for accessibility, SEO, security."""

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
def a11y(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Check accessibility (ARIA labels, alt texts, focus order, semantic HTML)."""
    import asyncio

    async def _a11y():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')
        
        audit_data = await connection.page.evaluate('''
            () => {
                const issues = [];
                
                // Check images for alt text
                const images = Array.from(document.images);
                const imagesWithoutAlt = images.filter(img => !img.alt && !img.getAttribute('aria-label'));
                imagesWithoutAlt.forEach(img => {
                    issues.push({
                        type: 'missing_alt',
                        element: 'img',
                        src: img.src,
                        message: 'Image missing alt text'
                    });
                });
                
                // Check form inputs for labels
                const inputs = Array.from(document.querySelectorAll('input, textarea, select'));
                inputs.forEach(input => {
                    const hasLabel = input.labels && input.labels.length > 0;
                    const hasAriaLabel = input.getAttribute('aria-label');
                    const hasAriaLabelledBy = input.getAttribute('aria-labelledby');
                    
                    if (!hasLabel && !hasAriaLabel && !hasAriaLabelledBy && input.type !== 'hidden') {
                        issues.push({
                            type: 'missing_label',
                            element: input.tagName.toLowerCase(),
                            id: input.id,
                            name: input.name,
                            message: 'Form input missing label'
                        });
                    }
                });
                
                // Check for proper heading hierarchy
                const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
                let lastLevel = 0;
                headings.forEach(h => {
                    const level = parseInt(h.tagName[1]);
                    if (level - lastLevel > 1) {
                        issues.push({
                            type: 'heading_skip',
                            element: h.tagName.toLowerCase(),
                            text: h.textContent.substring(0, 50),
                            message: `Heading level skipped from h${lastLevel} to h${level}`
                        });
                    }
                    lastLevel = level;
                });
                
                // Check for buttons without accessible names
                const buttons = Array.from(document.querySelectorAll('button, [role="button"]'));
                buttons.forEach(btn => {
                    const hasText = btn.textContent.trim().length > 0;
                    const hasAriaLabel = btn.getAttribute('aria-label');
                    const hasAriaLabelledBy = btn.getAttribute('aria-labelledby');
                    
                    if (!hasText && !hasAriaLabel && !hasAriaLabelledBy) {
                        issues.push({
                            type: 'button_no_name',
                            element: 'button',
                            message: 'Button has no accessible name'
                        });
                    }
                });
                
                // Check for links without href
                const links = Array.from(document.querySelectorAll('a'));
                links.forEach(link => {
                    if (!link.href || link.href === '#') {
                        issues.push({
                            type: 'empty_link',
                            element: 'a',
                            text: link.textContent.substring(0, 50),
                            message: 'Link has no href or empty href'
                        });
                    }
                });
                
                // Check for proper document structure
                const hasMain = document.querySelector('main, [role="main"]');
                const hasNav = document.querySelector('nav, [role="navigation"]');
                
                return {
                    issues: issues,
                    summary: {
                        totalIssues: issues.length,
                        missingAlt: issues.filter(i => i.type === 'missing_alt').length,
                        missingLabels: issues.filter(i => i.type === 'missing_label').length,
                        headingIssues: issues.filter(i => i.type === 'heading_skip').length,
                        buttonIssues: issues.filter(i => i.type === 'button_no_name').length,
                        linkIssues: issues.filter(i => i.type === 'empty_link').length
                    },
                    structure: {
                        hasMain: !!hasMain,
                        hasNav: !!hasNav
                    }
                };
            }
        ''')
        
        output_result({
            'accessibility': audit_data,
            'url': connection.page.url
        })

    asyncio.run(_a11y())


@app.command()
def seo(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Verify SEO meta tags, headings hierarchy, canonical URLs, robots."""
    import asyncio

    async def _seo():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')
        
        seo_data = await connection.page.evaluate('''
            () => {
                const getMeta = (name) => {
                    const meta = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
                    return meta ? meta.content : null;
                };
                
                const title = document.title;
                const description = getMeta('description');
                const keywords = getMeta('keywords');
                const canonical = document.querySelector('link[rel="canonical"]');
                const robots = getMeta('robots');
                
                // Open Graph tags
                const ogTitle = getMeta('og:title');
                const ogDescription = getMeta('og:description');
                const ogImage = getMeta('og:image');
                const ogUrl = getMeta('og:url');
                
                // Twitter cards
                const twitterCard = getMeta('twitter:card');
                const twitterTitle = getMeta('twitter:title');
                const twitterDescription = getMeta('twitter:description');
                const twitterImage = getMeta('twitter:image');
                
                // Headings
                const h1Count = document.querySelectorAll('h1').length;
                const h1Text = document.querySelector('h1')?.textContent.substring(0, 100);
                
                // Structured data
                const structuredData = Array.from(document.querySelectorAll('script[type="application/ld+json"]'))
                    .map(script => {
                        try {
                            return JSON.parse(script.textContent);
                        } catch (e) {
                            return null;
                        }
                    })
                    .filter(Boolean);
                
                const issues = [];
                if (!title || title.length < 10) issues.push('Title too short or missing');
                if (!description || description.length < 50) issues.push('Meta description too short or missing');
                if (h1Count === 0) issues.push('No H1 heading found');
                if (h1Count > 1) issues.push('Multiple H1 headings found');
                if (!canonical) issues.push('No canonical URL');
                
                return {
                    title: title,
                    titleLength: title.length,
                    description: description,
                    descriptionLength: description ? description.length : 0,
                    keywords: keywords,
                    canonical: canonical ? canonical.href : null,
                    robots: robots,
                    openGraph: {
                        title: ogTitle,
                        description: ogDescription,
                        image: ogImage,
                        url: ogUrl
                    },
                    twitter: {
                        card: twitterCard,
                        title: twitterTitle,
                        description: twitterDescription,
                        image: twitterImage
                    },
                    headings: {
                        h1Count: h1Count,
                        h1Text: h1Text
                    },
                    structuredData: structuredData,
                    issues: issues
                };
            }
        ''')
        
        output_result({
            'seo': seo_data,
            'url': connection.page.url
        })

    asyncio.run(_seo())


@app.command()
def security(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Check security headers (CSP, HSTS, X-Frame-Options)."""
    import asyncio

    async def _security():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        if url:
            response = await connection.page.goto(url, wait_until='domcontentloaded')
        else:
            response = None
        
        # Get response headers
        headers = {}
        if response:
            headers = response.headers
        
        security_headers = {
            'content-security-policy': headers.get('content-security-policy'),
            'strict-transport-security': headers.get('strict-transport-security'),
            'x-frame-options': headers.get('x-frame-options'),
            'x-content-type-options': headers.get('x-content-type-options'),
            'x-xss-protection': headers.get('x-xss-protection'),
            'referrer-policy': headers.get('referrer-policy'),
            'permissions-policy': headers.get('permissions-policy')
        }
        
        issues = []
        if not security_headers['content-security-policy']:
            issues.append('Missing Content-Security-Policy header')
        if not security_headers['strict-transport-security']:
            issues.append('Missing Strict-Transport-Security header (HSTS)')
        if not security_headers['x-frame-options']:
            issues.append('Missing X-Frame-Options header (clickjacking protection)')
        if not security_headers['x-content-type-options']:
            issues.append('Missing X-Content-Type-Options header')
        
        output_result({
            'security': {
                'headers': security_headers,
                'issues': issues,
                'score': max(0, 100 - (len(issues) * 20))
            },
            'url': connection.page.url
        })

    asyncio.run(_security())


@app.command()
def mixed(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Find HTTP resources on HTTPS pages (mixed content)."""
    import asyncio

    async def _mixed():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')
        
        mixed_content = await connection.page.evaluate('''
            () => {
                const pageProtocol = window.location.protocol;
                
                if (pageProtocol !== 'https:') {
                    return { isHttps: false, message: 'Page is not HTTPS' };
                }
                
                const httpResources = [];
                
                // Check images
                Array.from(document.images).forEach(img => {
                    if (img.src.startsWith('http://')) {
                        httpResources.push({ type: 'image', src: img.src });
                    }
                });
                
                // Check scripts
                Array.from(document.scripts).forEach(script => {
                    if (script.src && script.src.startsWith('http://')) {
                        httpResources.push({ type: 'script', src: script.src });
                    }
                });
                
                // Check stylesheets
                Array.from(document.styleSheets).forEach(sheet => {
                    if (sheet.href && sheet.href.startsWith('http://')) {
                        httpResources.push({ type: 'stylesheet', src: sheet.href });
                    }
                });
                
                // Check iframes
                Array.from(document.querySelectorAll('iframe')).forEach(iframe => {
                    if (iframe.src && iframe.src.startsWith('http://')) {
                        httpResources.push({ type: 'iframe', src: iframe.src });
                    }
                });
                
                return {
                    isHttps: true,
                    mixedContent: httpResources,
                    count: httpResources.length,
                    hasMixedContent: httpResources.length > 0
                };
            }
        ''')
        
        output_result({
            'mixedContent': mixed_content,
            'url': connection.page.url
        })

    asyncio.run(_mixed())


@app.command()
def links(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    max_check: int = typer.Option(50, help='Maximum number of links to check'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Find broken links (404s) on page."""
    import asyncio

    async def _links():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')
        
        # Get all links
        links_data = await connection.page.evaluate('''
            () => {
                const links = Array.from(document.links);
                return links.map(link => ({
                    href: link.href,
                    text: link.textContent.substring(0, 50)
                }));
            }
        ''')
        
        # Check links (limited to max_check)
        broken_links = []
        checked = 0
        
        for link_info in links_data[:max_check]:
            href = link_info['href']
            if not href or href.startswith('javascript:') or href.startswith('mailto:') or href.startswith('tel:'):
                continue
            
            try:
                response = await connection.page.request.get(href)
                if response.status >= 400:
                    broken_links.append({
                        'url': href,
                        'status': response.status,
                        'text': link_info['text']
                    })
                checked += 1
            except Exception as e:
                broken_links.append({
                    'url': href,
                    'error': str(e),
                    'text': link_info['text']
                })
                checked += 1
        
        output_result({
            'brokenLinks': broken_links,
            'summary': {
                'totalLinks': len(links_data),
                'checked': checked,
                'broken': len(broken_links)
            },
            'url': connection.page.url
        })

    asyncio.run(_links())


@app.command()
def images(
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Check images for missing alt text and oversized images."""
    import asyncio

    async def _images():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')
        
        images_data = await connection.page.evaluate('''
            () => {
                const images = Array.from(document.images);
                const issues = [];
                
                images.forEach(img => {
                    const imgIssues = [];
                    
                    // Check alt text
                    if (!img.alt && !img.getAttribute('aria-label')) {
                        imgIssues.push('missing_alt');
                    }
                    
                    // Check if image is larger than display size
                    if (img.naturalWidth > img.width * 2 || img.naturalHeight > img.height * 2) {
                        imgIssues.push('oversized');
                    }
                    
                    // Check lazy loading
                    const hasLazyLoading = img.loading === 'lazy' || img.getAttribute('data-src');
                    
                    if (imgIssues.length > 0) {
                        issues.push({
                            src: img.src,
                            alt: img.alt,
                            naturalWidth: img.naturalWidth,
                            naturalHeight: img.naturalHeight,
                            displayWidth: img.width,
                            displayHeight: img.height,
                            hasLazyLoading: hasLazyLoading,
                            issues: imgIssues
                        });
                    }
                });
                
                return {
                    totalImages: images.length,
                    imagesWithIssues: issues.length,
                    issues: issues,
                    summary: {
                        missingAlt: issues.filter(i => i.issues.includes('missing_alt')).length,
                        oversized: issues.filter(i => i.issues.includes('oversized')).length
                    }
                };
            }
        ''')
        
        output_result({
            'images': images_data,
            'url': connection.page.url
        })

    asyncio.run(_images())
