---
name: scrape-and-extract
description: Extract structured data (text, links, tables, images, attributes) from web pages using webscraper-cli.
---

# Scrape and Extract

Extract data from a single URL or a small set of elements.

## Trigger

The user wants to:
- Get the text of an element (h1, p, div, etc.)
- Extract all links from a page
- Get image URLs or alt text
- Extract table data into JSON or CSV
- Pull specific attributes like `href`, `src`, or `data-*`
- Get clean Markdown or stripped text from a page
- Extract structured data (JSON-LD, metadata, forms)

## Workflow

1. **Navigate and Extract**: Use `webscraper text` or `webscraper extract` with the `--url` flag.
   ```bash
   webscraper text "h1" --url "https://example.com"
   ```

2. **Format Selection**: Choose between `json`, `csv`, `plain`, or `table` using `--format`.
   ```bash
   webscraper extract links --url "https://example.com" --format csv
   ```

3. **Multiple Selectors**: Use `batch selectors` for pulling multiple different elements at once.
   ```bash
   webscraper batch selectors "h1,p,a" --url "https://example.com"
   ```

4. **Structured Content**: Use `extract` subcommands for specialized extractions.
   ```bash
   webscraper extract markdown --url "https://example.com"
   webscraper extract schema --url "https://example.com"
   webscraper extract forms --url "https://example.com"
   webscraper extract meta --url "https://example.com"
   webscraper extract xpath "//div/@class" --url "https://example.com"
   webscraper extract regex "\d{3}-\d{4}" --url "https://example.com"
   ```

5. **Proxy/User-Agent**: Use global options for sites that block default requests.
   ```bash
   webscraper --user-agent "MyBot/2.0" --proxy "http://proxy:8080" extract links --url "URL"
   ```

## Output

- Extracted data in the requested format (stdout)
- Error message with suggestion if selectors are not found or navigation fails
