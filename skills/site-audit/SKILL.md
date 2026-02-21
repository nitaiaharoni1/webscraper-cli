---
name: site-audit
description: Audit web pages for accessibility, SEO, security, broken links, and performance using webscraper-cli.
---

# Site Audit

Audit one or more pages for common issues like accessibility violations, SEO metadata, security headers, broken links, and performance metrics.

## Trigger

The user wants to:
- Check for accessibility (a11y) issues on a page
- Analyze SEO metadata (titles, descriptions, meta tags)
- Verify security headers
- Find and report broken links on a site
- Monitor page performance (Core Web Vitals, memory)
- Check for mixed content issues

## Workflow

1. **Audit Specific Categories**: Use `webscraper audit` followed by the category.
   ```bash
   webscraper audit a11y --url "https://example.com"
   webscraper audit seo --url "https://example.com"
   webscraper audit security --url "https://example.com"
   ```

2. **Broken Link Check**: Use `audit links` to find 404s and other dead links.
   ```bash
   webscraper audit links --url "https://example.com" --max-check 50
   ```

3. **Performance**: Use `audit vitals` or `audit memory` to check page speed and resources.
   ```bash
   webscraper audit vitals --url "https://example.com"
   webscraper audit memory --url "https://example.com"
   ```

4. **Full Audit**: Run multiple audit types on the same URL.
   ```bash
   webscraper audit a11y --url "URL"
   webscraper audit seo --url "URL"
   webscraper audit security --url "URL"
   webscraper audit links --url "URL"
   webscraper audit images --url "URL"
   webscraper audit mixed --url "URL"
   webscraper audit lighthouse --url "URL"
   ```

## Available Audit Commands

- `audit a11y` -- Accessibility violations
- `audit seo` -- SEO metadata analysis
- `audit security` -- Security headers check
- `audit mixed` -- Mixed content detection
- `audit links` -- Broken link finder
- `audit images` -- Image optimization check
- `audit vitals` -- Core Web Vitals
- `audit lighthouse` -- Lighthouse-style audit
- `audit memory` -- Memory usage analysis

## Output

- Detailed audit reports (JSON, CSV, or plain text)
- Performance metrics (Core Web Vitals)
- List of broken links with source/target URLs
