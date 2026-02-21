---
name: crawl-site
description: Scrape multiple pages, follow links, handle infinite scroll, or paginate through results using webscraper-cli.
---

# Crawl Site

Extract data from multiple pages or handle dynamically loaded lists.

## Trigger

The user wants to:
- Crawl an entire site to a specific depth
- Scrape data across many URLs provided in a file
- Extract results from a page with infinite scroll
- Automatically click "Next" buttons to paginate through results
- Process multiple URLs in parallel (concurrency)
- Parse sitemaps or RSS feeds

## Workflow

1. **Crawl a Domain**: Use `webscraper crawl site` with a starting URL and depth.
   ```bash
   webscraper crawl site "https://example.com" --depth 2 --extract "h1"
   ```

2. **Sitemap/RSS**: Parse structured feeds directly.
   ```bash
   webscraper crawl sitemap "https://example.com/sitemap.xml"
   webscraper crawl rss "https://example.com/feed.xml"
   ```

3. **Infinite Scroll**: Use `extract infinite` for pages that load content as you scroll down.
   ```bash
   webscraper extract infinite --url "https://example.com/gallery" --extract ".item" --max-items 100
   ```

4. **Auto-Pagination**: Use `extract paginate` to click a "Next" button repeatedly.
   ```bash
   webscraper extract paginate --url "https://example.com/blog" --next "a.next" --extract "h2" --max-pages 10
   ```

5. **Batch Processing**: Use `batch urls` with a file containing many URLs to scrape them all at once.
   ```bash
   webscraper batch urls urls.txt --extract "h1" --concurrency 5
   ```

6. **With Proxy**: Use proxy for large crawls to avoid rate limiting.
   ```bash
   webscraper --proxy "http://proxy:8080" crawl site "URL" --depth 3
   ```

## Output

- Extracted data from multiple pages (stdout or saved to a directory)
- Progress logs for crawl or batch operations
- Error reports for failed URLs (can be retried with `batch retry`)
