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
- Monitor page performance (vitals, memory)
- Highlight specific elements for debugging

## Workflow

1. **Audit Specific Categories**: Use `webscraper audit` followed by the category (`a11y`, `seo`, `security`, `links`, or `images`).
   ```bash
   webscraper audit a11y --url "https://example.com"
   webscraper audit seo --url "https://example.com"
   ```

2. **Broken Link Check**: Use `audit links` to find 404s and other dead links.
   ```bash
   webscraper audit links --url "https://example.com" --max-check 50
   ```

3. **Performance Monitoring**: Use `perf vitals` or `perf memory` to check page speed and resources.
   ```bash
   webscraper perf vitals --url "https://example.com"
   ```

4. **Visual Monitoring**: Use `monitor console` to catch browser logs or `monitor highlight` to see specific elements visually in the browser.
   ```bash
   webscraper monitor console --filter "error" --url "https://example.com"
   ```

## Output

- Detailed audit reports (JSON, CSV, or plain text)
- Performance metrics (Core Web Vitals)
- List of broken links with source/target URLs
- Error and warning logs
