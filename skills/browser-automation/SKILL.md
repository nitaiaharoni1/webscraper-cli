---
name: browser-automation
description: Automate multi-step browser interactions, form fills, clicks, and navigation using webscraper-cli.
---

# Browser Automation

Perform interactive tasks on websites like logging in, filling out forms, or navigating complex flows.

## Trigger

The user wants to:
- Log into a website
- Fill out and submit a form
- Click buttons or specific elements
- Hover, focus, or drag-and-drop elements
- Perform multi-step navigation while keeping the browser open

## Workflow

1. **Initial Navigation**: Start with `webscraper goto` to open the URL.
   ```bash
   webscraper goto "https://example.com/login"
   ```

2. **Wait for State**: Ensure the page is ready with `--wait-for` or `wait selector`.
   ```bash
   webscraper wait selector "input[name=email]"
   ```

3. **Recon**: Discover form fields before interacting.
   ```bash
   webscraper extract forms
   ```

4. **Interactions**: Use `interact type-text`, `click`, or `interact fill-form`.
   ```bash
   webscraper interact type-text "input[name=email]" "user@example.com"
   webscraper interact type-text "input[name=password]" "password123"
   webscraper click "button[type=submit]"
   ```

5. **Verify and Capture**: Check the result and optionally take a screenshot.
   ```bash
   webscraper extract text ".dashboard"
   webscraper capture dashboard.png
   ```

6. **Proxy/Auth**: Use global options for restricted sites.
   ```bash
   webscraper --proxy "http://proxy:8080" --user-agent "Mozilla/5.0 ..." goto "URL"
   ```

## Output

- Interaction status (stdout)
- Saved files (if using `capture` or `record`)
