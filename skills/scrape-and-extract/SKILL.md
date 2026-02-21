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

4. **Structured Content**: Use `content` commands for specialized extractions like Markdown or Schema.org data.
   ```bash
   webscraper content markdown --url "https://example.com"
   webscraper content schema --url "https://example.com"
   ```

## Output

- Extracted data in the requested format (stdout)
- Error message if selectors are not found or navigation fails
