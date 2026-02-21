"""Command registry with metadata, descriptions, and examples for all CLI commands."""

COMMAND_REGISTRY = {
    "navigation": {
        "description": "Browser navigation commands",
        "commands": {
            "goto": {
                "full_name": "navigate goto",
                "description": "Navigate to a URL",
                "usage": "cli.py navigate goto <URL> [OPTIONS]",
                "example": "cli.py navigate goto https://example.com --wait-until networkidle",
                "category": "navigation",
            },
            "back": {
                "full_name": "navigate back",
                "description": "Go back to the previous page",
                "usage": "cli.py navigate back [OPTIONS]",
                "example": "cli.py navigate back",
                "category": "navigation",
            },
            "forward": {
                "full_name": "navigate forward",
                "description": "Go forward to the next page",
                "usage": "cli.py navigate forward [OPTIONS]",
                "example": "cli.py navigate forward",
                "category": "navigation",
            },
            "reload": {
                "full_name": "navigate reload",
                "description": "Reload the current page",
                "usage": "cli.py navigate reload [OPTIONS]",
                "example": "cli.py navigate reload --hard",
                "category": "navigation",
            },
        },
    },
    "extraction": {
        "description": "Data extraction commands",
        "commands": {
            "text": {
                "full_name": "extract text",
                "description": "Extract text from elements matching selector",
                "usage": "cli.py extract text <SELECTOR> [OPTIONS]",
                "example": "cli.py extract text 'h1' --url https://example.com --all",
                "category": "extraction",
            },
            "links": {
                "full_name": "extract links",
                "description": "Extract all links from the page",
                "usage": "cli.py extract links [OPTIONS]",
                "example": "cli.py extract links --url https://example.com --format csv",
                "category": "extraction",
            },
            "html": {
                "full_name": "extract html",
                "description": "Extract HTML content from elements",
                "usage": "cli.py extract html <SELECTOR> [OPTIONS]",
                "example": "cli.py extract html '.content' --url https://example.com",
                "category": "extraction",
            },
            "attr": {
                "full_name": "extract attr",
                "description": "Extract attribute values from elements",
                "usage": "cli.py extract attr <SELECTOR> <ATTRIBUTE> [OPTIONS]",
                "example": "cli.py extract attr 'a' 'href' --all --url https://example.com",
                "category": "extraction",
            },
            "count": {
                "full_name": "extract count",
                "description": "Count elements matching selector",
                "usage": "cli.py extract count <SELECTOR> [OPTIONS]",
                "example": "cli.py extract count '.item' --url https://example.com",
                "category": "extraction",
            },
            "images": {
                "full_name": "extract images",
                "description": "Extract all images from the page",
                "usage": "cli.py extract images [OPTIONS]",
                "example": "cli.py extract images --url https://example.com",
                "category": "extraction",
            },
            "table": {
                "full_name": "extract table",
                "description": "Extract table data as JSON",
                "usage": "cli.py extract table <SELECTOR> [OPTIONS]",
                "example": "cli.py extract table 'table.data' --url https://example.com",
                "category": "extraction",
            },
            "table-csv": {
                "full_name": "extract table-csv",
                "description": "Extract HTML table and save directly to CSV",
                "usage": "cli.py extract table-csv <SELECTOR> <OUTPUT_FILE> [OPTIONS]",
                "example": "cli.py extract table-csv 'table' output.csv --url https://example.com",
                "category": "extraction",
            },
            "strip": {
                "full_name": "extract strip",
                "description": "Strip HTML and extract clean readable text",
                "usage": "cli.py extract strip <SELECTOR> [OPTIONS]",
                "example": "cli.py extract strip '.article' --url https://example.com",
                "category": "extraction",
            },
            "markdown": {
                "full_name": "extract markdown",
                "description": "Convert page to Markdown",
                "usage": "cli.py extract markdown <SELECTOR> [OPTIONS]",
                "example": "cli.py extract markdown '.content' --url https://example.com",
                "category": "extraction",
            },
            "meta": {
                "full_name": "extract meta",
                "description": "Extract meta tags and page metadata",
                "usage": "cli.py extract meta [OPTIONS]",
                "example": "cli.py extract meta --url https://example.com",
                "category": "extraction",
            },
            "schema": {
                "full_name": "extract schema",
                "description": "Extract structured data (JSON-LD, microdata)",
                "usage": "cli.py extract schema [OPTIONS]",
                "example": "cli.py extract schema --url https://example.com",
                "category": "extraction",
            },
            "xpath": {
                "full_name": "extract xpath",
                "description": "Extract elements using XPath",
                "usage": "cli.py extract xpath <XPATH> [OPTIONS]",
                "example": "cli.py extract xpath '//h1[@class=\"title\"]' --url https://example.com",
                "category": "extraction",
            },
            "regex": {
                "full_name": "extract regex",
                "description": "Extract text matching regex pattern",
                "usage": "cli.py extract regex <PATTERN> [OPTIONS]",
                "example": "cli.py extract regex '\\d{3}-\\d{3}-\\d{4}' --url https://example.com",
                "category": "extraction",
            },
            "forms": {
                "full_name": "extract forms",
                "description": "List all forms with fields and actions",
                "usage": "cli.py extract forms [OPTIONS]",
                "example": "cli.py extract forms --url https://example.com",
                "category": "extraction",
            },
            "expand": {
                "full_name": "extract expand",
                "description": "Expand all collapsible elements",
                "usage": "cli.py extract expand [OPTIONS]",
                "example": "cli.py extract expand --url https://example.com --selector 'details'",
                "category": "extraction",
            },
            "smart": {
                "full_name": "extract smart",
                "description": "Smart scrape with SPA support and clean text extraction",
                "usage": "cli.py extract smart [OPTIONS]",
                "example": "cli.py extract smart --url https://example.com --format json",
                "category": "extraction",
            },
            "info": {
                "full_name": "extract info",
                "description": "Get page information (URL, title, viewport)",
                "usage": "cli.py extract info [OPTIONS]",
                "example": "cli.py extract info --url https://example.com",
                "category": "extraction",
            },
            "infinite": {
                "full_name": "extract infinite",
                "description": "Auto-scroll infinite scroll pages and extract data",
                "usage": "cli.py extract infinite [OPTIONS]",
                "example": "cli.py extract infinite --extract '.item' --max-items 100 --url https://example.com",
                "category": "extraction",
            },
            "paginate": {
                "full_name": "extract paginate",
                "description": "Auto-paginate and extract data from multiple pages",
                "usage": "cli.py extract paginate [OPTIONS]",
                "example": "cli.py extract paginate --next 'a.next' --extract '.item' --max-pages 10",
                "category": "extraction",
            },
        },
    },
    "interaction": {
        "description": "User interaction commands",
        "commands": {
            "click": {
                "full_name": "interact click",
                "description": "Click an element",
                "usage": "cli.py interact click <SELECTOR> [OPTIONS]",
                "example": "cli.py interact click '.button' --url https://example.com",
                "category": "interaction",
            },
            "type-text": {
                "full_name": "interact type-text",
                "description": "Type text into an element",
                "usage": "cli.py interact type-text <SELECTOR> <TEXT> [OPTIONS]",
                "example": "cli.py interact type-text '#email' 'user@example.com' --url https://example.com",
                "category": "interaction",
            },
            "hover": {
                "full_name": "interact hover",
                "description": "Hover over an element",
                "usage": "cli.py interact hover <SELECTOR> [OPTIONS]",
                "example": "cli.py interact hover '.menu-item' --url https://example.com",
                "category": "interaction",
            },
            "scroll": {
                "full_name": "interact scroll",
                "description": "Scroll the page",
                "usage": "cli.py interact scroll [OPTIONS]",
                "example": "cli.py interact scroll --direction down --by 500",
                "category": "interaction",
            },
            "select": {
                "full_name": "interact select",
                "description": "Select an option in a dropdown",
                "usage": "cli.py interact select <SELECTOR> <VALUE> [OPTIONS]",
                "example": "cli.py interact select '#country' 'US' --url https://example.com",
                "category": "interaction",
            },
            "check": {
                "full_name": "interact check",
                "description": "Check a checkbox or radio button",
                "usage": "cli.py interact check <SELECTOR> [OPTIONS]",
                "example": "cli.py interact check '#agree' --url https://example.com",
                "category": "interaction",
            },
            "uncheck": {
                "full_name": "interact uncheck",
                "description": "Uncheck a checkbox",
                "usage": "cli.py interact uncheck <SELECTOR> [OPTIONS]",
                "example": "cli.py interact uncheck '#newsletter' --url https://example.com",
                "category": "interaction",
            },
            "press": {
                "full_name": "interact press",
                "description": "Press a keyboard key",
                "usage": "cli.py interact press <KEY> [OPTIONS]",
                "example": "cli.py interact press 'Enter' --url https://example.com",
                "category": "interaction",
            },
            "focus": {
                "full_name": "interact focus",
                "description": "Focus on an element",
                "usage": "cli.py interact focus <SELECTOR> [OPTIONS]",
                "example": "cli.py interact focus '#input' --url https://example.com",
                "category": "interaction",
            },
            "drag": {
                "full_name": "interact drag",
                "description": "Drag an element to a target element",
                "usage": "cli.py interact drag <SELECTOR> <TARGET> [OPTIONS]",
                "example": "cli.py interact drag '.item' '.dropzone' --url https://example.com",
                "category": "interaction",
            },
            "upload": {
                "full_name": "interact upload",
                "description": "Upload a file to a file input",
                "usage": "cli.py interact upload <SELECTOR> <FILE_PATH> [OPTIONS]",
                "example": "cli.py interact upload '#file-input' './document.pdf' --url https://example.com",
                "category": "interaction",
            },
            "keyboard": {
                "full_name": "interact keyboard",
                "description": "Press keyboard shortcuts (e.g., Control+C, Meta+V)",
                "usage": "cli.py interact keyboard <KEYS> [OPTIONS]",
                "example": "cli.py interact keyboard 'Control+C'",
                "category": "interaction",
            },
            "select-option": {
                "full_name": "interact select-option",
                "description": "Select option from dropdown by value, label, or index",
                "usage": "cli.py interact select-option <SELECTOR> [OPTIONS]",
                "example": "cli.py interact select-option 'select' --value 'option1'",
                "category": "interaction",
            },
            "pinch": {
                "full_name": "interact pinch",
                "description": "Simulate pinch-to-zoom gesture (touch)",
                "usage": "cli.py interact pinch [OPTIONS]",
                "example": "cli.py interact pinch --scale 2.0",
                "category": "interaction",
            },
            "fill-form": {
                "full_name": "interact fill-form",
                "description": "Auto-fill form from JSON/YAML data",
                "usage": "cli.py interact fill-form <SELECTOR> --data <FILE> [OPTIONS]",
                "example": "cli.py interact fill-form 'form#signup' --data form-data.json --url https://example.com",
                "category": "interaction",
            },
            "submit-form": {
                "full_name": "interact submit-form",
                "description": "Submit a form",
                "usage": "cli.py interact submit-form <SELECTOR> [OPTIONS]",
                "example": "cli.py interact submit-form 'form#login' --url https://example.com",
                "category": "interaction",
            },
        },
    },
    "human": {
        "description": "Human-like interaction commands",
        "commands": {
            "type": {
                "full_name": "human type",
                "description": "Type text with human-like delays and occasional typos",
                "usage": "cli.py human type <SELECTOR> <TEXT> [OPTIONS]",
                "example": "cli.py human type '#input' 'Hello World' --typo-chance 0.02",
                "category": "human",
            },
            "mouse": {
                "full_name": "human mouse",
                "description": "Move mouse with realistic bezier curve and perform action",
                "usage": "cli.py human mouse <SELECTOR> [OPTIONS]",
                "example": "cli.py human mouse '.button' --action click",
                "category": "human",
            },
            "drag": {
                "full_name": "human drag",
                "description": "Drag element from source to target with realistic timing",
                "usage": "cli.py human drag <SOURCE> <TARGET> [OPTIONS]",
                "example": "cli.py human drag '.item' '.target'",
                "category": "human",
            },
        },
    },
    "api": {
        "description": "Browser API execution commands",
        "commands": {
            "fetch": {
                "full_name": "api fetch",
                "description": "Execute fetch request from browser context (inherits cookies, auth, CORS)",
                "usage": "cli.py api fetch <URL> [OPTIONS]",
                "example": "cli.py api fetch 'https://api.example.com/data' --method GET",
                "category": "api",
            },
            "har": {
                "full_name": "api har",
                "description": "Export HTTP Archive (HAR) of network activity",
                "usage": "cli.py api har <OUTPUT_FILE> [OPTIONS]",
                "example": "cli.py api har output.har --url https://example.com",
                "category": "api",
            },
            "mock": {
                "full_name": "api mock",
                "description": "Mock API endpoints with custom responses",
                "usage": "cli.py api mock <PATTERN> [OPTIONS]",
                "example": "cli.py api mock '*/api/*' --response-json '{\"mocked\": true}' --status 200",
                "category": "api",
            },
        },
    },
    "inspection": {
        "description": "Element inspection commands",
        "commands": {
            "styles": {
                "full_name": "inspect styles",
                "description": "Get computed CSS styles for an element",
                "usage": "cli.py inspect styles <SELECTOR> [OPTIONS]",
                "example": "cli.py inspect styles 'h1' --properties 'color,font-size'",
                "category": "inspection",
            },
            "bounds": {
                "full_name": "inspect bounds",
                "description": "Get element bounding box (position and dimensions)",
                "usage": "cli.py inspect bounds <SELECTOR> [OPTIONS]",
                "example": "cli.py inspect bounds '.button'",
                "category": "inspection",
            },
            "contrast": {
                "full_name": "inspect contrast",
                "description": "Calculate color contrast ratio for WCAG compliance",
                "usage": "cli.py inspect contrast <SELECTOR> [OPTIONS]",
                "example": "cli.py inspect contrast 'p'",
                "category": "inspection",
            },
            "fonts": {
                "full_name": "inspect fonts",
                "description": "List all fonts used on the page",
                "usage": "cli.py inspect fonts [OPTIONS]",
                "example": "cli.py inspect fonts --url https://example.com",
                "category": "inspection",
            },
            "sw": {
                "full_name": "inspect sw",
                "description": "List service workers",
                "usage": "cli.py inspect sw [OPTIONS]",
                "example": "cli.py inspect sw --url https://example.com",
                "category": "inspection",
            },
        },
    },
    "audit": {
        "description": "Accessibility, SEO, security, and performance audit commands",
        "commands": {
            "a11y": {
                "full_name": "audit a11y",
                "description": "Check accessibility (ARIA labels, alt texts, focus order, semantic HTML)",
                "usage": "cli.py audit a11y [OPTIONS]",
                "example": "cli.py audit a11y --url https://example.com",
                "category": "audit",
            },
            "seo": {
                "full_name": "audit seo",
                "description": "Verify SEO meta tags, headings hierarchy, canonical URLs, robots",
                "usage": "cli.py audit seo [OPTIONS]",
                "example": "cli.py audit seo --url https://example.com",
                "category": "audit",
            },
            "security": {
                "full_name": "audit security",
                "description": "Check security headers (CSP, HSTS, X-Frame-Options)",
                "usage": "cli.py audit security [OPTIONS]",
                "example": "cli.py audit security --url https://example.com",
                "category": "audit",
            },
            "mixed": {
                "full_name": "audit mixed",
                "description": "Find HTTP resources on HTTPS pages (mixed content)",
                "usage": "cli.py audit mixed [OPTIONS]",
                "example": "cli.py audit mixed --url https://example.com",
                "category": "audit",
            },
            "links": {
                "full_name": "audit links",
                "description": "Find broken links (404s) on page",
                "usage": "cli.py audit links [OPTIONS]",
                "example": "cli.py audit links --url https://example.com --max-check 50",
                "category": "audit",
            },
            "images": {
                "full_name": "audit images",
                "description": "Check images for missing alt text and oversized images",
                "usage": "cli.py audit images [OPTIONS]",
                "example": "cli.py audit images --url https://example.com",
                "category": "audit",
            },
            "vitals": {
                "full_name": "audit vitals",
                "description": "Get Core Web Vitals (LCP, FID, CLS, TTFB)",
                "usage": "cli.py audit vitals [OPTIONS]",
                "example": "cli.py audit vitals --url https://example.com",
                "category": "audit",
            },
            "lighthouse": {
                "full_name": "audit lighthouse",
                "description": "Run basic performance audit",
                "usage": "cli.py audit lighthouse [OPTIONS]",
                "example": "cli.py audit lighthouse --url https://example.com",
                "category": "audit",
            },
            "memory": {
                "full_name": "audit memory",
                "description": "Get JavaScript heap usage and DOM node counts",
                "usage": "cli.py audit memory [OPTIONS]",
                "example": "cli.py audit memory --url https://example.com",
                "category": "audit",
            },
        },
    },
    "network": {
        "description": "Network interception and simulation commands",
        "commands": {
            "intercept": {
                "full_name": "network intercept",
                "description": "Intercept, block, or modify network requests",
                "usage": "cli.py network intercept [OPTIONS]",
                "example": "cli.py network intercept --block '*.ads.*' --url https://example.com",
                "category": "network",
            },
            "requests": {
                "full_name": "network requests",
                "description": "List all network requests",
                "usage": "cli.py network requests [OPTIONS]",
                "example": "cli.py network requests --filter 'api' --format table",
                "category": "network",
            },
            "headers": {
                "full_name": "network headers",
                "description": "Set custom request headers",
                "usage": "cli.py network headers <ACTION> [OPTIONS]",
                "example": "cli.py network headers set --name 'Authorization' --value 'Bearer xxx'",
                "category": "network",
            },
            "auth": {
                "full_name": "network auth",
                "description": "Set HTTP Basic Authentication credentials",
                "usage": "cli.py network auth --username <USER> --password <PASS> [OPTIONS]",
                "example": "cli.py network auth --username 'admin' --password 'secret' --url https://example.com",
                "category": "network",
            },
            "throttle": {
                "full_name": "network throttle",
                "description": "Simulate slow network conditions",
                "usage": "cli.py network throttle [OPTIONS]",
                "example": "cli.py network throttle --preset slow-3g --url https://example.com",
                "category": "network",
            },
            "offline": {
                "full_name": "network offline",
                "description": "Toggle offline mode",
                "usage": "cli.py network offline [OPTIONS]",
                "example": "cli.py network offline --enable true",
                "category": "network",
            },
            "websocket": {
                "full_name": "network websocket",
                "description": "Monitor WebSocket connections and messages",
                "usage": "cli.py network websocket [OPTIONS]",
                "example": "cli.py network websocket --url https://example.com --duration 10",
                "category": "network",
            },
        },
    },
    "screenshot": {
        "description": "Screenshot and visual capture commands",
        "commands": {
            "capture": {
                "full_name": "screenshot capture",
                "description": "Take a screenshot",
                "usage": "cli.py screenshot capture <FILENAME> [OPTIONS]",
                "example": "cli.py screenshot capture page.png --url https://example.com --full-page",
                "category": "screenshot",
            },
            "element": {
                "full_name": "screenshot element",
                "description": "Take a screenshot of a specific element",
                "usage": "cli.py screenshot element <SELECTOR> <FILENAME> [OPTIONS]",
                "example": "cli.py screenshot element 'h1' header.png --url https://example.com",
                "category": "screenshot",
            },
            "visual-diff": {
                "full_name": "screenshot visual-diff",
                "description": "Compare two screenshots and generate a visual diff",
                "usage": "cli.py screenshot visual-diff <IMAGE1> <IMAGE2> [OPTIONS]",
                "example": "cli.py screenshot visual-diff img1.png img2.png --output diff.png",
                "category": "screenshot",
            },
            "pdf": {
                "full_name": "screenshot pdf",
                "description": "Save page as PDF",
                "usage": "cli.py screenshot pdf <FILENAME> [OPTIONS]",
                "example": "cli.py screenshot pdf page.pdf --url https://example.com --format A4",
                "category": "screenshot",
            },
        },
    },
    "waiting": {
        "description": "Wait and synchronization commands",
        "commands": {
            "selector": {
                "full_name": "wait selector",
                "description": "Wait for element matching selector",
                "usage": "cli.py wait selector <SELECTOR> [OPTIONS]",
                "example": "cli.py wait selector '.content' --url https://example.com --state visible",
                "category": "waiting",
            },
            "timeout": {
                "full_name": "wait timeout",
                "description": "Wait for specified duration",
                "usage": "cli.py wait timeout <MILLISECONDS> [OPTIONS]",
                "example": "cli.py wait timeout 2000",
                "category": "waiting",
            },
            "navigation": {
                "full_name": "wait navigation",
                "description": "Wait for page navigation",
                "usage": "cli.py wait navigation [OPTIONS]",
                "example": "cli.py wait navigation --url https://example.com",
                "category": "waiting",
            },
            "idle": {
                "full_name": "wait idle",
                "description": "Wait for network idle (no network activity for 500ms)",
                "usage": "cli.py wait idle [OPTIONS]",
                "example": "cli.py wait idle --url https://example.com",
                "category": "waiting",
            },
            "animation": {
                "full_name": "wait animation",
                "description": "Wait for CSS animations to complete",
                "usage": "cli.py wait animation [OPTIONS]",
                "example": "cli.py wait animation --selector '.animated'",
                "category": "waiting",
            },
        },
    },
    "recording": {
        "description": "Recording and replay commands",
        "commands": {
            "start": {
                "full_name": "record start",
                "description": "Start recording user actions",
                "usage": "cli.py record start [OPTIONS]",
                "example": "cli.py record start --output recording.json --url https://example.com",
                "category": "recording",
            },
            "stop": {
                "full_name": "record stop",
                "description": "Stop recording and save actions",
                "usage": "cli.py record stop [OPTIONS]",
                "example": "cli.py record stop",
                "category": "recording",
            },
            "replay": {
                "full_name": "record replay",
                "description": "Replay recorded actions",
                "usage": "cli.py record replay <INPUT_FILE> [OPTIONS]",
                "example": "cli.py record replay recording.json --speed 1.5",
                "category": "recording",
            },
            "video-start": {
                "full_name": "record video-start",
                "description": "Start video recording of browser session",
                "usage": "cli.py record video-start [OPTIONS]",
                "example": "cli.py record video-start --output recording.webm --url https://example.com",
                "category": "recording",
            },
            "video-stop": {
                "full_name": "record video-stop",
                "description": "Stop video recording and save file",
                "usage": "cli.py record video-stop [OPTIONS]",
                "example": "cli.py record video-stop",
                "category": "recording",
            },
            "video-context": {
                "full_name": "record video-context",
                "description": "Start a new browser context with video recording enabled",
                "usage": "cli.py record video-context [OPTIONS]",
                "example": "cli.py record video-context --output-dir ./videos --url https://example.com",
                "category": "recording",
            },
        },
    },
    "tabs": {
        "description": "Tab management commands",
        "commands": {
            "open": {
                "full_name": "tabs open",
                "description": "Open a new tab",
                "usage": "cli.py tabs open [OPTIONS]",
                "example": "cli.py tabs open --url https://example.com",
                "category": "tabs",
            },
            "close": {
                "full_name": "tabs close",
                "description": "Close a tab",
                "usage": "cli.py tabs close [OPTIONS]",
                "example": "cli.py tabs close --index 1",
                "category": "tabs",
            },
            "switch": {
                "full_name": "tabs switch",
                "description": "Switch to a different tab",
                "usage": "cli.py tabs switch <INDEX> [OPTIONS]",
                "example": "cli.py tabs switch 0",
                "category": "tabs",
            },
            "list": {
                "full_name": "tabs list",
                "description": "List all open tabs",
                "usage": "cli.py tabs list [OPTIONS]",
                "example": "cli.py tabs list",
                "category": "tabs",
            },
        },
    },
    "crawling": {
        "description": "Web crawling commands",
        "commands": {
            "site": {
                "full_name": "crawl site",
                "description": "Crawl a website following links",
                "usage": "cli.py crawl site <URL> [OPTIONS]",
                "example": "cli.py crawl site https://example.com --depth 2 --extract '.content'",
                "category": "crawling",
            },
            "sitemap": {
                "full_name": "crawl sitemap",
                "description": "Parse sitemap.xml and return URLs",
                "usage": "cli.py crawl sitemap <URL> [OPTIONS]",
                "example": "cli.py crawl sitemap https://example.com/sitemap.xml",
                "category": "crawling",
            },
            "rss": {
                "full_name": "crawl rss",
                "description": "Parse RSS/Atom feed",
                "usage": "cli.py crawl rss <URL> [OPTIONS]",
                "example": "cli.py crawl rss https://example.com/feed.xml",
                "category": "crawling",
            },
        },
    },
    "batch": {
        "description": "Batch operations for parallel execution",
        "commands": {
            "urls": {
                "full_name": "batch urls",
                "description": "Scrape multiple URLs in parallel",
                "usage": "cli.py batch urls <FILE> [OPTIONS]",
                "example": "cli.py batch urls urls.txt --extract '.content' --concurrency 5",
                "category": "batch",
            },
            "selectors": {
                "full_name": "batch selectors",
                "description": "Extract multiple selectors at once",
                "usage": "cli.py batch selectors <SELECTORS> --url <URL> [OPTIONS]",
                "example": "cli.py batch selectors 'h1,p,a' --url https://example.com",
                "category": "batch",
            },
            "script": {
                "full_name": "batch script",
                "description": "Run commands from a script file",
                "usage": "cli.py batch script <FILE> [OPTIONS]",
                "example": "cli.py batch script script.yaml",
                "category": "batch",
            },
            "retry": {
                "full_name": "batch retry",
                "description": "Auto-retry failed operations",
                "usage": "cli.py batch retry <COMMAND> [OPTIONS]",
                "example": "cli.py batch retry 'cli.py goto https://example.com' --max-attempts 3",
                "category": "batch",
            },
        },
    },
    "clipboard": {
        "description": "Clipboard operations",
        "commands": {
            "copy": {
                "full_name": "clipboard copy",
                "description": "Copy text to clipboard",
                "usage": "cli.py clipboard copy <SELECTOR> [OPTIONS]",
                "example": "cli.py clipboard copy 'h1' --url https://example.com",
                "category": "clipboard",
            },
            "paste": {
                "full_name": "clipboard paste",
                "description": "Paste from clipboard into input",
                "usage": "cli.py clipboard paste <SELECTOR> [OPTIONS]",
                "example": "cli.py clipboard paste 'input[name=email]'",
                "category": "clipboard",
            },
            "select-text": {
                "full_name": "clipboard select-text",
                "description": "Select text range in element",
                "usage": "cli.py clipboard select-text <SELECTOR> [OPTIONS]",
                "example": "cli.py clipboard select-text 'p' --start 0 --end 50",
                "category": "clipboard",
            },
        },
    },
    "download": {
        "description": "File download and export commands",
        "commands": {
            "file": {
                "full_name": "download file",
                "description": "Download file from URL or button",
                "usage": "cli.py download file [OPTIONS]",
                "example": "cli.py download file --url https://example.com/file.pdf --output-dir ./downloads",
                "category": "download",
            },
            "export": {
                "full_name": "download export",
                "description": "Export extracted data to file",
                "usage": "cli.py download export <TYPE> [OPTIONS]",
                "example": "cli.py download export links --format csv --output links.csv",
                "category": "download",
            },
            "save-html": {
                "full_name": "download save-html",
                "description": "Save page HTML to file",
                "usage": "cli.py download save-html --output <FILE> [OPTIONS]",
                "example": "cli.py download save-html --output page.html",
                "category": "download",
            },
        },
    },
    "emulation": {
        "description": "Browser emulation commands",
        "commands": {
            "device": {
                "full_name": "emulate device",
                "description": "Emulate device (iPhone, iPad, etc.)",
                "usage": "cli.py emulate device <DEVICE> [OPTIONS]",
                "example": "cli.py emulate device 'iPhone 14' --url https://example.com",
                "category": "emulation",
            },
            "viewport": {
                "full_name": "emulate viewport",
                "description": "Set viewport size",
                "usage": "cli.py emulate viewport --width <W> --height <H> [OPTIONS]",
                "example": "cli.py emulate viewport --width 1920 --height 1080",
                "category": "emulation",
            },
            "geolocation": {
                "full_name": "emulate geolocation",
                "description": "Set geolocation",
                "usage": "cli.py emulate geolocation --lat <LAT> --lon <LON> [OPTIONS]",
                "example": "cli.py emulate geolocation --lat 40.7128 --lon -74.0060 --url https://example.com",
                "category": "emulation",
            },
            "responsive": {
                "full_name": "emulate responsive",
                "description": "Take screenshots at multiple viewport sizes",
                "usage": "cli.py emulate responsive [OPTIONS]",
                "example": "cli.py emulate responsive --url https://example.com --output-dir screenshots",
                "category": "emulation",
            },
            "dark-mode": {
                "full_name": "emulate dark-mode",
                "description": "Toggle prefers-color-scheme",
                "usage": "cli.py emulate dark-mode [OPTIONS]",
                "example": "cli.py emulate dark-mode --enable true --url https://example.com",
                "category": "emulation",
            },
            "reduced-motion": {
                "full_name": "emulate reduced-motion",
                "description": "Toggle prefers-reduced-motion",
                "usage": "cli.py emulate reduced-motion [OPTIONS]",
                "example": "cli.py emulate reduced-motion --enable true",
                "category": "emulation",
            },
            "print-preview": {
                "full_name": "emulate print-preview",
                "description": "Trigger print media emulation",
                "usage": "cli.py emulate print-preview [OPTIONS]",
                "example": "cli.py emulate print-preview --url https://example.com --output page.pdf",
                "category": "emulation",
            },
            "contrast": {
                "full_name": "emulate contrast",
                "description": "Toggle prefers-contrast",
                "usage": "cli.py emulate contrast [OPTIONS]",
                "example": "cli.py emulate contrast --enable true --url https://example.com",
                "category": "emulation",
            },
        },
    },
    "shadow": {
        "description": "Shadow DOM commands",
        "commands": {
            "access": {
                "full_name": "shadow access",
                "description": "Access elements inside Shadow DOM",
                "usage": "cli.py shadow access <SELECTOR> [OPTIONS]",
                "example": "cli.py shadow access 'my-component' --selector '.inner' --url https://example.com",
                "category": "shadow",
            }
        },
    },
    "shortcuts": {
        "description": "Top-level shortcut commands",
        "commands": {
            "goto": {
                "full_name": "goto",
                "description": "Navigate to a URL (shortcut for navigate goto)",
                "usage": "cli.py goto <URL> [OPTIONS]",
                "example": "cli.py goto https://example.com --wait-until networkidle",
                "category": "shortcuts",
            },
            "click": {
                "full_name": "click",
                "description": "Click an element (shortcut for interact click)",
                "usage": "cli.py click <SELECTOR> [OPTIONS]",
                "example": "cli.py click '.button' --url https://example.com",
                "category": "shortcuts",
            },
            "text": {
                "full_name": "text",
                "description": "Extract text from elements (shortcut for extract text)",
                "usage": "cli.py text <SELECTOR> [OPTIONS]",
                "example": "cli.py text 'h1' --url https://example.com --all",
                "category": "shortcuts",
            },
            "capture": {
                "full_name": "capture",
                "description": "Take a screenshot (shortcut for screenshot capture)",
                "usage": "cli.py capture <FILENAME> [OPTIONS]",
                "example": "cli.py capture page.png --url https://example.com --full-page",
                "category": "shortcuts",
            },
        },
    },
}


def get_all_commands():
    """Get a flat list of all commands."""
    all_commands = []
    for category_name, category_data in COMMAND_REGISTRY.items():
        for cmd_name, cmd_data in category_data["commands"].items():
            all_commands.append({**cmd_data, "category": category_name})
    return all_commands


def get_command_by_name(full_name: str):
    """Get command metadata by full name (e.g., 'navigate goto')."""
    for category_data in COMMAND_REGISTRY.values():
        for cmd_data in category_data["commands"].values():
            if cmd_data["full_name"] == full_name:
                return cmd_data
    return None


def get_commands_by_category(category: str):
    """Get all commands in a category."""
    if category not in COMMAND_REGISTRY:
        return []
    return list(COMMAND_REGISTRY[category]["commands"].values())


def get_total_command_count():
    """Get total number of commands."""
    return sum(len(cat["commands"]) for cat in COMMAND_REGISTRY.values())
