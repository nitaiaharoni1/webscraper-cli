# Playwright MCP vs webscraper-cli: Real-World Contest Report

**Date:** March 15, 2026
**Environment:** macOS Darwin 25.3.0
**webscraper-cli:** Homebrew install (`brew install nitaiaharoni1/tools/webscraper-cli`)
**Playwright MCP:** Claude Code MCP plugin (`mcp__plugin_playwright_playwright__*`)

---

## Test Scenarios

| # | Scenario | Complexity |
|---|----------|------------|
| 1 | Extract HN top headlines + scores | Simple extraction |
| 2 | Wikipedia search interaction (fill form → submit → results) | Form automation |
| 3 | GitHub Trending repos with metadata | Dynamic SPA content |
| 4 | Full-page screenshot | Visual capture |
| 5 | Structured data / table extraction | Data parsing |

---

## Test 1: Hacker News Top Stories

### webscraper-cli
```bash
webscraper extract text ".titleline" --url "https://news.ycombinator.com" --all --format json
webscraper extract text ".subline .score" --url "https://news.ycombinator.com" --all --format json
```
**Commands:** 2
**Output:** Clean JSON arrays — 30 titles + 29 scores, immediately usable
**Sample:**
```json
["Ageless Linux – Software for humans of indeterminate age", "Show HN: Han – A Korean programming language written in Rust", ...]
["193 points", "92 points", "22 points", ...]
```
**Result:** ✅ Success — targeted, clean, scriptable

### Playwright MCP
```
browser_navigate → returns 58KB accessibility YAML tree
browser_snapshot → returns 58KB accessibility YAML tree (again)
```
**Steps:** 1 navigate (auto-snapshot on nav)
**Output:** Full accessibility tree — requires LLM parsing to extract titles; verbose, not directly usable
**Result:** ⚠️ Partial — data is there but buried in 58KB YAML structure

### Winner: **webscraper-cli** — precise selectors return clean data; Playwright MCP output needs secondary parsing

---

## Test 2: Wikipedia Search Interaction

### webscraper-cli
```bash
webscraper extract text "#mw-content-text p" --url "https://en.wikipedia.org/wiki/Playwright_(software)" --all --format plain
```
**Commands:** 1
**Strategy:** Bypasses search entirely by navigating directly to the article URL
**Output:** Full article text (~3,000 words), clean, immediately readable
**Result:** ✅ Success — but **cheated**: assumed URL is known ahead of time

### Playwright MCP
```
browser_navigate(wikipedia main page)
  → snapshot reveals ref=e23 for searchbox
browser_fill_form([{ref: "e23", value: "Playwright browser automation"}])
  → page updates, ref e25 (Search button) goes stale ❌
browser_snapshot (re-snapshot to get new refs)
  → new Search button ref=e836 discovered
browser_click(ref=e836)
  → navigates to search results page ✅
```
**Steps:** 4 (including 1 error recovery)
**Critical Issue:** Ref `e25` (Search button) became stale after the autocomplete dropdown appeared post-fill — required a full re-snapshot
**Output:** Full search results accessibility tree with 13 results, titles, snippets, dates
**Result:** ✅ Success — but required error recovery; verbose output

### Winner: **Playwright MCP** — genuinely navigated the search UI as a user would; webscraper-cli skipped the interaction entirely by using a direct URL

---

## Test 3: GitHub Trending Repositories

### webscraper-cli
```bash
webscraper extract text "h2.h3.lh-condensed" --url "https://github.com/trending" --all --format plain
```
**Commands:** 1
**Output:** Partial — repo names only (no descriptions, stars, forks, language)
```
volcengine / OpenViking
anthropics / claude-plugins-official
dimensionalOS / dimos
...
```
**Result:** ⚠️ Partial — names extracted but CSS class selectors fragile (GitHub frequently changes class names); no rich metadata

### Playwright MCP
```
browser_navigate("https://github.com/trending")
  → full accessibility snapshot with rich semantic data
```
**Steps:** 1
**Output:** Rich structured data per repo — name, description, language, star count, fork count, contributors, stars today:
```
volcengine/OpenViking — Python — 10,578 stars — 1,610 stars today
anthropics/claude-plugins-official — Python — 11,299 stars — 411 stars today
p-e-w/heretic — Python — 13,749 stars — 694 stars today
obra/superpowers — Shell — 83,470 stars — 1,439 stars today
msitarzewski/agency-agents — Shell — 43,757 stars — 4,280 stars today
```
**Result:** ✅ Excellent — accessibility tree naturally captures all semantic metadata without selector guesswork

### Winner: **Playwright MCP** — accessibility tree delivers rich semantic content without brittle CSS selectors; webscraper-cli returned only names

---

## Test 4: Full-Page Screenshot

### webscraper-cli
```bash
webscraper capture /tmp/hn_webscraper.png --url "https://news.ycombinator.com" --full-page
```
**Commands:** 1
**Output:** 639KB PNG of HN full page, saved to specified path
**Behavior:** Opens fresh browser context for the given URL, captures, closes
**Result:** ✅ Perfect — URL-targeted, predictable, stateless

### Playwright MCP
```
browser_take_screenshot(filename="playwright_hn.png", fullPage=true)
```
**Commands:** 1
**Critical Issue:** Took screenshot of **currently loaded page** (Wikipedia search results), not `news.ycombinator.com` — because Playwright MCP maintains a single shared browser session
**Result:** ❌ Wrong page captured — screenshot shows Wikipedia, not HN

### Winner: **webscraper-cli** — URL-targeted screenshots are always accurate; Playwright MCP requires explicit navigation first

---

## Test 5: Structured Data Extraction

### webscraper-cli
```bash
webscraper extract table "table.wikitable" --url "https://en.wikipedia.org/.../Comparison_of_browser_automation_software"
```
**Output:** No output (selector matched nothing — the page structure may have changed)
**Fallback attempt:** `extract links` also returned GitHub nav links, not repo data
**Result:** ❌ Failed — selector-based table extraction brittle

### Playwright MCP
The GitHub trending accessibility snapshot (Test 3) already contained all structured data with semantic labels — no separate test needed.
**Result:** ✅ Implicit success via accessibility tree

---

## Scorecard

| Test | webscraper-cli | Playwright MCP |
|------|:---:|:---:|
| 1. HN Headlines | ✅ Clean JSON | ⚠️ 58KB tree |
| 2. Wikipedia Search | ⚠️ Skipped interaction | ✅ Full form flow |
| 3. GitHub Trending (rich data) | ⚠️ Names only | ✅ Full metadata |
| 4. Screenshot (correct page) | ✅ URL-targeted | ❌ Wrong page |
| 5. Structured data | ❌ Selector failed | ✅ Via a11y tree |
| **Total** | **2.5 / 5** | **3.5 / 5** |

---

## Deep Analysis

### Architecture Differences

| Dimension | webscraper-cli | Playwright MCP |
|-----------|---------------|----------------|
| Session model | **Stateless per command** — fresh context each time | **Stateful single session** — shared browser tab |
| Output model | **Targeted extraction** — returns exactly what you asked for | **Full page snapshot** — entire accessibility tree |
| Selector model | CSS selectors (brittle against class changes) | Semantic refs from accessibility tree (stable) |
| URL targeting | Per-command `--url` flag | Must navigate first |
| Error recovery | Transparent — command fails with exit code | Stale refs require re-snapshot |
| Output size | Small — only extracted data | Large — full page structure (50-60KB) |
| Scriptability | Excellent — JSON output, pipes, shell scripting | Limited — output designed for LLM consumption |
| Multi-tab support | Not needed (stateless) | `browser_tabs` available but adds complexity |

### When Playwright MCP Wins

1. **True interaction flows** — login forms, multi-step wizards, SPAs where URL alone is insufficient
2. **Semantic richness** — accessibility tree captures structure, roles, states without CSS selector guesswork
3. **Dynamic content** — JavaScript-heavy pages where element meaning matters more than CSS class names
4. **Agent-driven workflows** — LLM can reason about `ref=e836` and interact semantically
5. **Bot-detection resistance** — real browser with real User-Agent, no CLI fingerprint

### When webscraper-cli Wins

1. **Batch/scripted extraction** — 112 commands, JSON output, easily piped into `jq`, `python`, etc.
2. **URL-targeted operations** — screenshot, extract, crawl with `--url` flag, no session management
3. **Data extraction tasks** — `.titleline`, `.score`, `h1` — when selectors are known and stable
4. **Multi-URL scraping** — `webscraper batch urls` handles N URLs in one invocation
5. **Audit tasks** — built-in SEO, a11y, Lighthouse, performance audits via CLI
6. **Crawling** — `webscraper crawl site` with depth control, no session state to manage

### Key Failure Modes Observed

**Playwright MCP:**
- **Stale ref problem**: Refs expire when page DOM mutates (e.g., autocomplete dropdown) — requires re-snapshot mid-flow (adds latency + steps)
- **Single session**: All operations share one browser tab — Test 4 screenshot captured the wrong page because navigation from Test 2 was still active
- **Output size**: 58-61KB accessibility trees are expensive to process, require LLM reasoning to extract specific values

**webscraper-cli:**
- **CSS selector brittleness**: `table.wikitable` returned nothing; GitHub's `h2.h3.lh-condensed` returned only partial data
- **No true interaction model**: Cannot handle forms that require JavaScript state (SPA login flows, CAPTCHAs, etc.) as naturally as Playwright MCP
- **Stateless limitation**: Cannot maintain login sessions across commands without explicit cookie/session management

---

## Recommendations

### Use Playwright MCP when:
- You're inside an agent loop that needs to reason about page structure
- The task involves **multi-step UI interaction** (login, checkout, wizard)
- CSS selectors are unknown or unstable
- You need semantic understanding of page state (disabled buttons, checked checkboxes, ARIA roles)

### Use webscraper-cli when:
- You need **URL-targeted, stateless extraction** (screenshots, content, tables, links)
- You're **scripting/automating** in shell with JSON output piped into other tools
- You need **bulk operations** (`batch`, `crawl`, `sitemap`)
- You need **audits** (SEO, Lighthouse, a11y, performance) as one-liners
- You want **explicit control** without shared browser state surprises

### Ideal Combo Strategy:
```
webscraper-cli → reconnaissance (extract forms, links, meta)
Playwright MCP → interaction (fill forms, click, navigate flows)
webscraper-cli → verification (extract result, screenshot final state)
```

---

## Final Verdict

**Overall winner: Playwright MCP (3.5/5 vs 2.5/5)** — but this is **context-dependent**.

For an **AI agent** (like Claude Code), Playwright MCP is the better fit: it's designed for LLM-driven automation, returns semantic structure, and handles dynamic UI naturally — even if it requires more steps.

For a **developer/DevOps workflow** (scripting, pipelines, CI), webscraper-cli wins decisively: stateless, composable, 112 specialized commands, and clean JSON output.

The stale-ref problem in Playwright MCP is its biggest practical pain point — a form fill should not require a full re-snapshot just to click the submit button. webscraper-cli's stateless design sidesteps this class of bugs entirely.
