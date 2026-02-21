# Web Scraper CLI

Powerful CLI tool for website scraping, automation, and crawling using Playwright.

## Installation

### Using Homebrew (Recommended)

```bash
brew tap nitaiaharoni1/tools
brew install nitaiaharoni1/tools/webscraper-cli
```

Then use: `webscraper --help`

### Manual Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Quick Start

```bash
# Navigate and extract (headed/visible by default, browser stays open)
webscraper goto "https://example.com"
webscraper text "h1" --url "https://example.com"

# Extract links as CSV
webscraper extract links --url "https://example.com" --format csv

# Batch operations
webscraper batch selectors "h1,p,a" --url "https://example.com"

# Run in headless mode (invisible browser, faster for automation)
webscraper --headless goto "https://example.com"
```

## Browser Behavior

**By default:**
- Browser opens in **headed mode** (visible window)
- Browser **stays open** after each command
- Subsequent commands **reuse the same browser** (fast!)

This allows you to:
- See what's happening in the browser
- Run multiple commands without browser restart overhead
- Maintain session state (cookies, page) across commands
- Use `--headless` for invisible automation when needed

**To close the browser:**
```bash
pkill -f "remote-debugging-port"
```

The browser will close when:
- You terminate the process (Ctrl+C)
- The Python process exits
- You use the cleanup handler in `cli.py`

## Global Options

All commands support these global options:

- `--verbose/-v` - Show debug information
- `--quiet/-q` - Suppress output except errors
- `--format/-f` - Output format: json, csv, plain, table (default: json)
- `--timeout` - Global timeout in milliseconds (default: 30000)
- `--headless/--headed` - Run in headless mode (default: headed/visible)

## Commands

### Navigation

```bash
# Navigate to URL
webscraper goto "https://example.com"

# Navigate with wait conditions
webscraper goto "https://example.com" --wait-for "h1" --wait-until networkidle

# Back/Forward/Reload
webscraper navigate back
webscraper navigate forward
webscraper navigate reload
```

### Extraction

```bash
# Extract text
webscraper text "h1" --url "https://example.com"
webscraper text "p" --all --format plain  # Extract all paragraphs

# Extract links (CSV format)
webscraper extract links --url "https://example.com" --format csv

# Extract attributes
webscraper extract attr "a" "href" --all --url "https://example.com"

# Extract images
webscraper extract images --url "https://example.com"

# Extract table data
webscraper extract table "table.data" --url "https://example.com"

# Count elements
webscraper extract count "p" --url "https://example.com"

# Extract HTML
webscraper extract html --url "https://example.com" --selector "body"
```

### Interactions

```bash
# Click
webscraper click "button" --url "https://example.com"

# Type text
webscraper interact type-text "input[name=q]" "search query" --url "https://google.com"

# Form interactions
webscraper interact select "select#country" "US" --url "https://example.com"
webscraper interact check "input[type=checkbox]"
webscraper interact uncheck "input[type=checkbox]"

# Keyboard
webscraper interact press "Enter"
webscraper interact press "Escape"

# Mouse
webscraper interact hover "a.link"
webscraper interact focus "input[name=email]"
webscraper interact drag "#source" "#target"

# Scroll
webscraper interact scroll --by 500
webscraper interact scroll --to "footer"

# Upload file
webscraper interact upload "input[type=file]" "/path/to/file.pdf"
```

### Screenshots

```bash
# Screenshot
webscraper capture page.png --url "https://example.com"

# Full page screenshot
webscraper capture page.png --url "https://example.com" --full-page

# Element screenshot
webscraper capture element.png --url "https://example.com" --selector "h1"
```

### Waiting

```bash
# Wait for element
webscraper wait selector "h1" --url "https://example.com"

# Wait for timeout
webscraper wait timeout 5000

# Wait for navigation
webscraper wait navigation --url "https://example.com"
```

### JavaScript Evaluation

```bash
# Run JavaScript
webscraper eval run "document.title" --url "https://example.com"

# Run from file
webscraper eval run "" --file script.js --url "https://example.com"
```

### Page Operations

```bash
# Get page info
webscraper page info --url "https://example.com"

# Save as PDF
webscraper page pdf document.pdf --url "https://example.com"
```

### Storage

```bash
# Cookies
webscraper storage cookies get --url "https://example.com"
webscraper storage cookies set "name" "value" --url "https://example.com"
webscraper storage cookies clear --url "https://example.com"

# LocalStorage
webscraper storage localstorage get --url "https://example.com"
webscraper storage localstorage set "key" "value" --url "https://example.com"
webscraper storage localstorage clear --url "https://example.com"
```

### Batch Operations

```bash
# Extract multiple selectors at once
webscraper batch selectors "h1,p,a" --url "https://example.com"

# Scrape multiple URLs in parallel
echo "https://example.com" > urls.txt
echo "https://example.org" >> urls.txt
webscraper batch urls urls.txt --extract "h1" --concurrency 5

# Run script file (YAML)
webscraper batch script workflow.yaml
```

**Script file format (workflow.yaml):**
```yaml
steps:
  - goto: "https://example.com"
  - extract:
      selector: "h1"
      output: "title.json"
  - click: "button.submit"
  - wait:
      selector: ".result"
  - capture: "result.png"
```

### Crawling

```bash
# Crawl site
webscraper crawl site "https://example.com" --depth 2 --extract "h1" --output data/

# Crawl with filters
webscraper crawl site "https://example.com" --follow "*/products/*" --exclude "*/login/*"
```

### Frames

```bash
# List frames
webscraper frame list-frames --url "https://example.com"

# Switch to iframe
webscraper frame switch "iframe#content"

# Switch back to main
webscraper frame main
```

### Dialogs

```bash
# Accept dialog
webscraper dialog accept --url "https://example.com"

# Accept prompt with text
webscraper dialog accept --text "response" --url "https://example.com"

# Dismiss dialog
webscraper dialog dismiss --url "https://example.com"
```

### Assertions

```bash
# Assert element exists
webscraper assert exists "h1" --url "https://example.com"

# Assert text content
webscraper assert text "h1" --contains "Welcome"
webscraper assert text "h1" --equals "Example Domain"

# Assert count
webscraper assert count "p" --equals 2
webscraper assert count "li" --min 5
webscraper assert count "div" --max 10

# Assert visibility
webscraper assert visible "button.submit"
```

### Daemon Mode (Performance)

```bash
# Start daemon (persistent browser)
webscraper daemon start --port 9222

# Connect to daemon (fast - no browser launch overhead)
webscraper daemon connect

# Check status
webscraper daemon status

# Stop daemon
webscraper daemon stop
```

## Output Formats

- `json` - JSON output (default)
- `csv` - CSV format (for lists of objects)
- `plain` - Plain text
- `table` - Formatted table (using Rich)

## Examples

### Complete Workflow

```bash
# Navigate, extract, and screenshot
webscraper goto "https://example.com"
webscraper text "h1" --format plain
webscraper extract links --format csv > links.csv
webscraper capture page.png
```

### Form Automation

```bash
# Fill and submit form
webscraper interact type-text "input[name=email]" "user@example.com" --url "https://example.com/form"
webscraper interact type-text "input[name=password]" "password123" --url "https://example.com/form"
webscraper interact check "input[type=checkbox]" --url "https://example.com/form"
webscraper interact press "Enter" --url "https://example.com/form"
```

### Data Scraping

```bash
# Extract structured data
webscraper extract table "table.data" --url "https://example.com/data" --format csv > data.csv
webscraper extract images --url "https://example.com/gallery" --format json
webscraper extract attr "a.product-link" "href" --all --url "https://example.com/products"
```

### Batch Processing

```bash
# Scrape multiple pages
webscraper batch urls urls.txt --extract "h1" --concurrency 10 --format json > results.json

# Extract multiple selectors
webscraper batch selectors "h1.title,p.description,a.link" --url "https://example.com"
```

### Testing/Validation

```bash
# Assert page loaded correctly
webscraper assert exists "h1" --url "https://example.com"
webscraper assert text "h1" --equals "Example Domain"
webscraper assert count "p" --min 1
```

## Performance Tips

1. **Browser persistence** (default) - Browser stays open between commands for faster execution

2. **Use daemon mode** for long-running workflows:
   ```bash
   webscraper daemon start
   webscraper goto "https://example.com"  # Fast - reuses browser
   ```

3. **Batch operations** for parallel processing:
   ```bash
   webscraper batch urls urls.txt --concurrency 10
   ```

4. **Use headless mode** (`--headless`) for faster execution in automation

5. **Optimize selectors** - Use specific selectors instead of generic ones

## New Advanced Operations

### Content Extraction & Transformation

```bash
# Strip HTML and get clean readable text
webscraper content strip --selector "article" --url "https://example.com"

# Convert page to Markdown
webscraper content markdown --output article.md --url "https://example.com"

# Extract meta tags (SEO, Open Graph, Twitter Cards)
webscraper content meta --url "https://example.com"

# Extract structured data (JSON-LD, microdata)
webscraper content schema --url "https://example.com"

# Query by XPath
webscraper content xpath "//div[@class='item']/a/@href" --text

# Extract text matching regex pattern
webscraper content regex "\d{3}-\d{4}" --selector "body"

# List all forms with fields
webscraper content forms --url "https://example.com"
```

### Clipboard & Selection

```bash
# Copy text to clipboard
webscraper clipboard copy "h1"

# Paste from clipboard into input
webscraper clipboard paste "input[name=email]"

# Select text range in element
webscraper clipboard select-text "p" --start 0 --end 50
```

### Downloads & Export

```bash
# Download file from URL or button
webscraper download file --url "https://example.com/file.pdf" --output-dir ./downloads
webscraper download file --selector "a.download" --output-dir ./downloads

# Export extracted data to file
webscraper download export links --format csv --output links.csv
webscraper download export images --format json --output images.json

# Save page HTML to file
webscraper download save-html --output page.html
```

### Network & Requests

```bash
# Intercept/block network requests
webscraper network intercept --block "*.ads.*" --url "https://example.com"

# List all network requests
webscraper network requests --filter "api" --format table

# Set custom headers
webscraper network headers set --name "Authorization" --value "Bearer xxx"

# Set HTTP Basic Auth
webscraper network auth --username "admin" --password "secret" --url "https://example.com"
```

### Browser Emulation

```bash
# Emulate device (iPhone, iPad, etc.)
webscraper emulate device "iPhone 14" --url "https://example.com"

# Set viewport size
webscraper emulate viewport --width 1920 --height 1080

# Set geolocation
webscraper emulate geolocation --lat 40.7128 --lon -74.0060 --url "https://example.com"
```

### Form Automation

```bash
# Auto-fill form from JSON/YAML
webscraper form fill "form#signup" --data form-data.json --url "https://example.com"

# Submit form
webscraper form submit "form#login" --url "https://example.com"
```

### Advanced Scrolling

```bash
# Auto-scroll infinite scroll pages
webscraper scroll infinite --extract ".item" --max-items 100 --url "https://example.com"

# Auto-paginate and extract
webscraper scroll paginate --next "a.next" --extract ".item" --max-pages 10
```

### Shadow DOM

```bash
# Access elements inside Shadow DOM
webscraper shadow access "my-component" --selector ".inner" --url "https://example.com"
```

### Monitoring & Debugging

```bash
# Capture console logs
webscraper monitor console --filter "error" --url "https://example.com"

# Get performance metrics
webscraper monitor performance --url "https://example.com"

# Highlight elements (visual debugging)
webscraper monitor highlight "a.broken" --color red

# Record actions for replay
webscraper monitor record start --output actions.yaml
webscraper monitor record stop --output actions.yaml
webscraper monitor record replay --output actions.yaml
```

### Comparison & Snapshots

```bash
# Save page snapshot
webscraper compare snapshot --output snap1.json --url "https://example.com"

# Compare two snapshots
webscraper compare diff --snapshot1 snap1.json --snapshot2 snap2.json --format unified
```

## New Features (50+ Operations)

### Screenshot Enhancements

```bash
# Element-specific screenshot
webscraper screenshot element "h1" screenshot.png

# Full page screenshot (scrolling)
webscraper screenshot fullpage page.png

# Visual diff between screenshots
webscraper screenshot visual-diff img1.png img2.png --output diff.png
```

### Browser API Execution

```bash
# Execute fetch from browser context (inherits cookies/auth)
webscraper api fetch "https://api.example.com/data" --method GET

# Export HTTP Archive (HAR)
webscraper api har output.har --url "https://example.com"

# Mock API endpoints
webscraper api mock "*/api/*" --response-json '{"mocked": true}' --status 200
```

### Performance Analysis

```bash
# Get Core Web Vitals
webscraper perf vitals --url "https://example.com"

# Run performance audit
webscraper perf lighthouse --url "https://example.com"

# Get memory usage
webscraper perf memory --url "https://example.com"
```

### Element Inspection

```bash
# Get computed styles
webscraper inspect styles "h1" --properties "color,font-size"

# Get element bounds
webscraper inspect bounds ".button"

# Check color contrast (WCAG)
webscraper inspect contrast "p"

# List fonts used
webscraper inspect fonts --url "https://example.com"

# List service workers
webscraper inspect sw --url "https://example.com"
```

### Human-like Interaction

```bash
# Type with realistic delays and typos
webscraper human type "input" "Hello World" --typo-chance 0.02

# Move mouse with bezier curves
webscraper human mouse ".button" --action click

# Drag with realistic timing
webscraper human drag ".item" ".target"
```

### Accessibility & Audits

```bash
# Accessibility audit
webscraper audit a11y --url "https://example.com"

# SEO audit
webscraper audit seo --url "https://example.com"

# Security headers check
webscraper audit security --url "https://example.com"

# Find mixed content
webscraper audit mixed --url "https://example.com"

# Find broken links
webscraper audit links --url "https://example.com" --max-check 50

# Image optimization audit
webscraper audit images --url "https://example.com"
```

### Network Simulation

```bash
# Throttle network speed
webscraper network throttle --preset slow-3g --url "https://example.com"

# Toggle offline mode
webscraper network offline --enable true

# Monitor WebSocket connections
webscraper network websocket --url "https://example.com" --duration 10
```

### Recording & Replay

```bash
# Record user actions (JSON format)
webscraper record start --output recording.json --url "https://example.com"
webscraper record stop
webscraper record replay recording.json --speed 1.5

# Video recording (screen capture)
webscraper record video-start --output recording.webm --url "https://example.com"
webscraper record video-stop

# Create browser context with video recording
webscraper record video-context --output-dir ./videos --url "https://example.com"
```

### Tab & History Management

```bash
# Open new tab
webscraper tabs open --url "https://example.com"

# Close tab
webscraper tabs close --index 1

# Switch tabs
webscraper tabs switch 0

# List all tabs
webscraper tabs list

# Navigate history
webscraper tabs back
webscraper tabs forward
webscraper tabs history
```

### Visual Testing

```bash
# Responsive screenshots (all viewports)
webscraper visual responsive --url "https://example.com" --output-dir screenshots

# Toggle dark mode
webscraper visual dark-mode --enable true --url "https://example.com"

# Toggle reduced motion
webscraper visual reduced-motion --enable true

# Print preview
webscraper visual print-preview --output page.pdf

# Set custom viewport
webscraper visual viewport --width 1920 --height 1080

# Toggle high contrast
webscraper visual contrast --enable true
```

### Enhanced Interactions

```bash
# Keyboard shortcuts
webscraper interact keyboard "Control+C"

# Select dropdown option
webscraper interact select-option "select" --value "option1"

# Pinch to zoom (touch gesture)
webscraper interact pinch --scale 2.0
```

### Enhanced Extraction

```bash
# Extract social meta tags
webscraper extract social --url "https://example.com"

# Export table to CSV
webscraper extract table-csv "table" output.csv --url "https://example.com"
```

### Enhanced Crawling

```bash
# Parse sitemap.xml
webscraper crawl sitemap "https://example.com/sitemap.xml"

# Parse RSS feed
webscraper crawl rss "https://example.com/feed.xml"
```

### Enhanced Waiting

```bash
# Wait for network idle
webscraper wait idle --url "https://example.com"

# Wait for animations to complete
webscraper wait animation --selector ".animated"
```

### Enhanced Batch Operations

```bash
# Retry failed operations
webscraper batch retry "webscraper goto https://example.com" --max-attempts 3
```

### Conditional Flow Control

```bash
# Conditional execution
webscraper flow if ".error" --then-command "echo Error found" --else-command "echo Success"

# Check element existence
webscraper flow exists ".button" --url "https://example.com"

# Loop through elements
webscraper flow loop ".item" --command "echo Processing item $INDEX"
```

### Local Server

```bash
# Start local HTTP server
webscraper serve start --directory ./public --port 8000

# Start proxy server
webscraper serve proxy --target "https://example.com" --port 8080
```

## Command Reference

| Category | Commands |
|----------|----------|
| **Navigation** | goto, navigate (back, forward, reload), tabs (open, close, switch, list, back, forward, history) |
| **Extraction** | text, extract (text, links, html, attr, images, table, count, social, table-csv) |
| **Content** | content (strip, markdown, meta, schema, xpath, regex, forms) |
| **Interactions** | click, interact (type-text, hover, scroll, select, check, uncheck, press, focus, drag, upload, keyboard, select-option, pinch) |
| **Human-like** | human (type, mouse, drag) |
| **Clipboard** | clipboard (copy, paste, select-text) |
| **Downloads** | download (file, export, save-html) |
| **Network** | network (intercept, requests, headers, auth, throttle, offline, websocket) |
| **API** | api (fetch, har, mock) |
| **Emulation** | emulate (device, viewport, geolocation) |
| **Forms** | form (fill, submit) |
| **Scrolling** | scroll (infinite, paginate) |
| **Shadow DOM** | shadow (access) |
| **Monitoring** | monitor (console, performance, highlight, record) |
| **Performance** | perf (vitals, lighthouse, memory) |
| **Inspection** | inspect (styles, bounds, contrast, fonts, sw) |
| **Audits** | audit (a11y, seo, security, mixed, links, images) |
| **Visual Testing** | visual (responsive, dark-mode, reduced-motion, print-preview, viewport, contrast) |
| **Recording** | record (start, stop, replay, video-start, video-stop, video-context) |
| **Comparison** | compare (snapshot, diff) |
| **Screenshots** | capture, screenshot (capture, element, fullpage, visual-diff) |
| **Waiting** | wait (selector, timeout, navigation, idle, animation) |
| **JavaScript** | eval (run) |
| **Page** | page (info, pdf) |
| **Storage** | storage (cookies, localstorage) |
| **Batch** | batch (urls, script, selectors, retry) |
| **Crawling** | crawl (site, sitemap, rss) |
| **Flow Control** | flow (if, exists, loop) |
| **Server** | serve (start, proxy) |
| **Frames** | frame (switch, main, list-frames) |
| **Dialogs** | dialog (accept, dismiss) |
| **Assertions** | assert (exists, text, count, visible) |
| **Daemon** | daemon (start, stop, status, connect) |
