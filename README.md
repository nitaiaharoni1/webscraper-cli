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
python3 cli.py goto "https://example.com"
python3 cli.py text "h1" --url "https://example.com"

# Extract links as CSV
python3 cli.py extract links --url "https://example.com" --format csv

# Batch operations
python3 cli.py batch selectors "h1,p,a" --url "https://example.com"

# Run in headless mode (invisible browser, faster for automation)
python3 cli.py --headless goto "https://example.com"
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
python3 cli.py goto "https://example.com"

# Navigate with wait conditions
python3 cli.py goto "https://example.com" --wait-for "h1" --wait-until networkidle

# Back/Forward/Reload
python3 cli.py navigate back
python3 cli.py navigate forward
python3 cli.py navigate reload
```

### Extraction

```bash
# Extract text
python3 cli.py text "h1" --url "https://example.com"
python3 cli.py text "p" --all --format plain  # Extract all paragraphs

# Extract links (CSV format)
python3 cli.py extract links --url "https://example.com" --format csv

# Extract attributes
python3 cli.py extract attr "a" "href" --all --url "https://example.com"

# Extract images
python3 cli.py extract images --url "https://example.com"

# Extract table data
python3 cli.py extract table "table.data" --url "https://example.com"

# Count elements
python3 cli.py extract count "p" --url "https://example.com"

# Extract HTML
python3 cli.py extract html --url "https://example.com" --selector "body"
```

### Interactions

```bash
# Click
python3 cli.py click "button" --url "https://example.com"

# Type text
python3 cli.py interact type-text "input[name=q]" "search query" --url "https://google.com"

# Form interactions
python3 cli.py interact select "select#country" "US" --url "https://example.com"
python3 cli.py interact check "input[type=checkbox]"
python3 cli.py interact uncheck "input[type=checkbox]"

# Keyboard
python3 cli.py interact press "Enter"
python3 cli.py interact press "Escape"

# Mouse
python3 cli.py interact hover "a.link"
python3 cli.py interact focus "input[name=email]"
python3 cli.py interact drag "#source" "#target"

# Scroll
python3 cli.py interact scroll --by 500
python3 cli.py interact scroll --to "footer"

# Upload file
python3 cli.py interact upload "input[type=file]" "/path/to/file.pdf"
```

### Screenshots

```bash
# Screenshot
python3 cli.py capture page.png --url "https://example.com"

# Full page screenshot
python3 cli.py capture page.png --url "https://example.com" --full-page

# Element screenshot
python3 cli.py capture element.png --url "https://example.com" --selector "h1"
```

### Waiting

```bash
# Wait for element
python3 cli.py wait selector "h1" --url "https://example.com"

# Wait for timeout
python3 cli.py wait timeout 5000

# Wait for navigation
python3 cli.py wait navigation --url "https://example.com"
```

### JavaScript Evaluation

```bash
# Run JavaScript
python3 cli.py eval run "document.title" --url "https://example.com"

# Run from file
python3 cli.py eval run "" --file script.js --url "https://example.com"
```

### Page Operations

```bash
# Get page info
python3 cli.py page info --url "https://example.com"

# Save as PDF
python3 cli.py page pdf document.pdf --url "https://example.com"
```

### Storage

```bash
# Cookies
python3 cli.py storage cookies get --url "https://example.com"
python3 cli.py storage cookies set "name" "value" --url "https://example.com"
python3 cli.py storage cookies clear --url "https://example.com"

# LocalStorage
python3 cli.py storage localstorage get --url "https://example.com"
python3 cli.py storage localstorage set "key" "value" --url "https://example.com"
python3 cli.py storage localstorage clear --url "https://example.com"
```

### Batch Operations

```bash
# Extract multiple selectors at once
python3 cli.py batch selectors "h1,p,a" --url "https://example.com"

# Scrape multiple URLs in parallel
echo "https://example.com" > urls.txt
echo "https://example.org" >> urls.txt
python3 cli.py batch urls urls.txt --extract "h1" --concurrency 5

# Run script file (YAML)
python3 cli.py batch script workflow.yaml
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
python3 cli.py crawl site "https://example.com" --depth 2 --extract "h1" --output data/

# Crawl with filters
python3 cli.py crawl site "https://example.com" --follow "*/products/*" --exclude "*/login/*"
```

### Frames

```bash
# List frames
python3 cli.py frame list-frames --url "https://example.com"

# Switch to iframe
python3 cli.py frame switch "iframe#content"

# Switch back to main
python3 cli.py frame main
```

### Dialogs

```bash
# Accept dialog
python3 cli.py dialog accept --url "https://example.com"

# Accept prompt with text
python3 cli.py dialog accept --text "response" --url "https://example.com"

# Dismiss dialog
python3 cli.py dialog dismiss --url "https://example.com"
```

### Assertions

```bash
# Assert element exists
python3 cli.py assert exists "h1" --url "https://example.com"

# Assert text content
python3 cli.py assert text "h1" --contains "Welcome"
python3 cli.py assert text "h1" --equals "Example Domain"

# Assert count
python3 cli.py assert count "p" --equals 2
python3 cli.py assert count "li" --min 5
python3 cli.py assert count "div" --max 10

# Assert visibility
python3 cli.py assert visible "button.submit"
```

### Daemon Mode (Performance)

```bash
# Start daemon (persistent browser)
python3 cli.py daemon start --port 9222

# Connect to daemon (fast - no browser launch overhead)
python3 cli.py daemon connect

# Check status
python3 cli.py daemon status

# Stop daemon
python3 cli.py daemon stop
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
python3 cli.py goto "https://example.com"
python3 cli.py text "h1" --format plain
python3 cli.py extract links --format csv > links.csv
python3 cli.py capture page.png
```

### Form Automation

```bash
# Fill and submit form
python3 cli.py interact type-text "input[name=email]" "user@example.com" --url "https://example.com/form"
python3 cli.py interact type-text "input[name=password]" "password123" --url "https://example.com/form"
python3 cli.py interact check "input[type=checkbox]" --url "https://example.com/form"
python3 cli.py interact press "Enter" --url "https://example.com/form"
```

### Data Scraping

```bash
# Extract structured data
python3 cli.py extract table "table.data" --url "https://example.com/data" --format csv > data.csv
python3 cli.py extract images --url "https://example.com/gallery" --format json
python3 cli.py extract attr "a.product-link" "href" --all --url "https://example.com/products"
```

### Batch Processing

```bash
# Scrape multiple pages
python3 cli.py batch urls urls.txt --extract "h1" --concurrency 10 --format json > results.json

# Extract multiple selectors
python3 cli.py batch selectors "h1.title,p.description,a.link" --url "https://example.com"
```

### Testing/Validation

```bash
# Assert page loaded correctly
python3 cli.py assert exists "h1" --url "https://example.com"
python3 cli.py assert text "h1" --equals "Example Domain"
python3 cli.py assert count "p" --min 1
```

## Performance Tips

1. **Browser persistence** (default) - Browser stays open between commands for faster execution

2. **Use daemon mode** for long-running workflows:
   ```bash
   python3 cli.py daemon start
   python3 cli.py goto "https://example.com"  # Fast - reuses browser
   ```

3. **Batch operations** for parallel processing:
   ```bash
   python3 cli.py batch urls urls.txt --concurrency 10
   ```

4. **Use headless mode** (`--headless`) for faster execution in automation

5. **Optimize selectors** - Use specific selectors instead of generic ones

## New Advanced Operations

### Content Extraction & Transformation

```bash
# Strip HTML and get clean readable text
python3 cli.py content strip --selector "article" --url "https://example.com"

# Convert page to Markdown
python3 cli.py content markdown --output article.md --url "https://example.com"

# Extract meta tags (SEO, Open Graph, Twitter Cards)
python3 cli.py content meta --url "https://example.com"

# Extract structured data (JSON-LD, microdata)
python3 cli.py content schema --url "https://example.com"

# Query by XPath
python3 cli.py content xpath "//div[@class='item']/a/@href" --text

# Extract text matching regex pattern
python3 cli.py content regex "\d{3}-\d{4}" --selector "body"

# List all forms with fields
python3 cli.py content forms --url "https://example.com"
```

### Clipboard & Selection

```bash
# Copy text to clipboard
python3 cli.py clipboard copy "h1"

# Paste from clipboard into input
python3 cli.py clipboard paste "input[name=email]"

# Select text range in element
python3 cli.py clipboard select-text "p" --start 0 --end 50
```

### Downloads & Export

```bash
# Download file from URL or button
python3 cli.py download file --url "https://example.com/file.pdf" --output-dir ./downloads
python3 cli.py download file --selector "a.download" --output-dir ./downloads

# Export extracted data to file
python3 cli.py download export links --format csv --output links.csv
python3 cli.py download export images --format json --output images.json

# Save page HTML to file
python3 cli.py download save-html --output page.html
```

### Network & Requests

```bash
# Intercept/block network requests
python3 cli.py network intercept --block "*.ads.*" --url "https://example.com"

# List all network requests
python3 cli.py network requests --filter "api" --format table

# Set custom headers
python3 cli.py network headers set --name "Authorization" --value "Bearer xxx"

# Set HTTP Basic Auth
python3 cli.py network auth --username "admin" --password "secret" --url "https://example.com"
```

### Browser Emulation

```bash
# Emulate device (iPhone, iPad, etc.)
python3 cli.py emulate device "iPhone 14" --url "https://example.com"

# Set viewport size
python3 cli.py emulate viewport --width 1920 --height 1080

# Set geolocation
python3 cli.py emulate geolocation --lat 40.7128 --lon -74.0060 --url "https://example.com"
```

### Form Automation

```bash
# Auto-fill form from JSON/YAML
python3 cli.py form fill "form#signup" --data form-data.json --url "https://example.com"

# Submit form
python3 cli.py form submit "form#login" --url "https://example.com"
```

### Advanced Scrolling

```bash
# Auto-scroll infinite scroll pages
python3 cli.py scroll infinite --extract ".item" --max-items 100 --url "https://example.com"

# Auto-paginate and extract
python3 cli.py scroll paginate --next "a.next" --extract ".item" --max-pages 10
```

### Shadow DOM

```bash
# Access elements inside Shadow DOM
python3 cli.py shadow access "my-component" --selector ".inner" --url "https://example.com"
```

### Monitoring & Debugging

```bash
# Capture console logs
python3 cli.py monitor console --filter "error" --url "https://example.com"

# Get performance metrics
python3 cli.py monitor performance --url "https://example.com"

# Highlight elements (visual debugging)
python3 cli.py monitor highlight "a.broken" --color red

# Record actions for replay
python3 cli.py monitor record start --output actions.yaml
python3 cli.py monitor record stop --output actions.yaml
python3 cli.py monitor record replay --output actions.yaml
```

### Comparison & Snapshots

```bash
# Save page snapshot
python3 cli.py compare snapshot --output snap1.json --url "https://example.com"

# Compare two snapshots
python3 cli.py compare diff --snapshot1 snap1.json --snapshot2 snap2.json --format unified
```

## New Features (50+ Operations)

### Screenshot Enhancements

```bash
# Element-specific screenshot
python3 cli.py screenshot element "h1" screenshot.png

# Full page screenshot (scrolling)
python3 cli.py screenshot fullpage page.png

# Visual diff between screenshots
python3 cli.py screenshot visual-diff img1.png img2.png --output diff.png
```

### Browser API Execution

```bash
# Execute fetch from browser context (inherits cookies/auth)
python3 cli.py api fetch "https://api.example.com/data" --method GET

# Export HTTP Archive (HAR)
python3 cli.py api har output.har --url "https://example.com"

# Mock API endpoints
python3 cli.py api mock "*/api/*" --response-json '{"mocked": true}' --status 200
```

### Performance Analysis

```bash
# Get Core Web Vitals
python3 cli.py perf vitals --url "https://example.com"

# Run performance audit
python3 cli.py perf lighthouse --url "https://example.com"

# Get memory usage
python3 cli.py perf memory --url "https://example.com"
```

### Element Inspection

```bash
# Get computed styles
python3 cli.py inspect styles "h1" --properties "color,font-size"

# Get element bounds
python3 cli.py inspect bounds ".button"

# Check color contrast (WCAG)
python3 cli.py inspect contrast "p"

# List fonts used
python3 cli.py inspect fonts --url "https://example.com"

# List service workers
python3 cli.py inspect sw --url "https://example.com"
```

### Human-like Interaction

```bash
# Type with realistic delays and typos
python3 cli.py human type "input" "Hello World" --typo-chance 0.02

# Move mouse with bezier curves
python3 cli.py human mouse ".button" --action click

# Drag with realistic timing
python3 cli.py human drag ".item" ".target"
```

### Accessibility & Audits

```bash
# Accessibility audit
python3 cli.py audit a11y --url "https://example.com"

# SEO audit
python3 cli.py audit seo --url "https://example.com"

# Security headers check
python3 cli.py audit security --url "https://example.com"

# Find mixed content
python3 cli.py audit mixed --url "https://example.com"

# Find broken links
python3 cli.py audit links --url "https://example.com" --max-check 50

# Image optimization audit
python3 cli.py audit images --url "https://example.com"
```

### Network Simulation

```bash
# Throttle network speed
python3 cli.py network throttle --preset slow-3g --url "https://example.com"

# Toggle offline mode
python3 cli.py network offline --enable true

# Monitor WebSocket connections
python3 cli.py network websocket --url "https://example.com" --duration 10
```

### Recording & Replay

```bash
# Record user actions (JSON format)
python3 cli.py record start --output recording.json --url "https://example.com"
python3 cli.py record stop
python3 cli.py record replay recording.json --speed 1.5

# Video recording (screen capture)
python3 cli.py record video-start --output recording.webm --url "https://example.com"
python3 cli.py record video-stop

# Create browser context with video recording
python3 cli.py record video-context --output-dir ./videos --url "https://example.com"
```

### Tab & History Management

```bash
# Open new tab
python3 cli.py tabs open --url "https://example.com"

# Close tab
python3 cli.py tabs close --index 1

# Switch tabs
python3 cli.py tabs switch 0

# List all tabs
python3 cli.py tabs list

# Navigate history
python3 cli.py tabs back
python3 cli.py tabs forward
python3 cli.py tabs history
```

### Visual Testing

```bash
# Responsive screenshots (all viewports)
python3 cli.py visual responsive --url "https://example.com" --output-dir screenshots

# Toggle dark mode
python3 cli.py visual dark-mode --enable true --url "https://example.com"

# Toggle reduced motion
python3 cli.py visual reduced-motion --enable true

# Print preview
python3 cli.py visual print-preview --output page.pdf

# Set custom viewport
python3 cli.py visual viewport --width 1920 --height 1080

# Toggle high contrast
python3 cli.py visual contrast --enable true
```

### Enhanced Interactions

```bash
# Keyboard shortcuts
python3 cli.py interact keyboard "Control+C"

# Select dropdown option
python3 cli.py interact select-option "select" --value "option1"

# Pinch to zoom (touch gesture)
python3 cli.py interact pinch --scale 2.0
```

### Enhanced Extraction

```bash
# Extract social meta tags
python3 cli.py extract social --url "https://example.com"

# Export table to CSV
python3 cli.py extract table-csv "table" output.csv --url "https://example.com"
```

### Enhanced Crawling

```bash
# Parse sitemap.xml
python3 cli.py crawl sitemap "https://example.com/sitemap.xml"

# Parse RSS feed
python3 cli.py crawl rss "https://example.com/feed.xml"
```

### Enhanced Waiting

```bash
# Wait for network idle
python3 cli.py wait idle --url "https://example.com"

# Wait for animations to complete
python3 cli.py wait animation --selector ".animated"
```

### Enhanced Batch Operations

```bash
# Retry failed operations
python3 cli.py batch retry "python3 cli.py goto https://example.com" --max-attempts 3
```

### Conditional Flow Control

```bash
# Conditional execution
python3 cli.py flow if ".error" --then-command "echo Error found" --else-command "echo Success"

# Check element existence
python3 cli.py flow exists ".button" --url "https://example.com"

# Loop through elements
python3 cli.py flow loop ".item" --command "echo Processing item $INDEX"
```

### Local Server

```bash
# Start local HTTP server
python3 cli.py serve start --directory ./public --port 8000

# Start proxy server
python3 cli.py serve proxy --target "https://example.com" --port 8080
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
