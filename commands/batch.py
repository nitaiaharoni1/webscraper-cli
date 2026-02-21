"""Batch operations for parallel execution."""

import asyncio
import json
import os
from typing import List, Optional

import typer

from core.async_command import get_connection, run_async
from core.browser import get_browser_manager
from core.output import output_json
from core.progress import create_progress, log_verbose
from core.settings import settings

app = typer.Typer()


@app.command()
def urls(
    file: str = typer.Argument(..., help="File containing URLs (one per line)"),
    extract: Optional[str] = typer.Option(None, "--extract", "-e", help="Selector to extract from each URL"),
    concurrency: int = typer.Option(5, "--concurrency", "-c", help="Number of parallel requests"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Scrape multiple URLs in parallel."""

    async def _batch_urls():
        # Read URLs from file
        if not os.path.exists(file):
            output_json({"error": f"File not found: {file}"})
            return

        with open(file, "r") as f:
            urls = [line.strip() for line in f if line.strip()]

        if not urls:
            output_json({"error": "No URLs found in file"})
            return

        results = []

        async def process_url(url: str):
            """Process a single URL."""
            connection = await get_connection(f"{session_id or 'batch'}-{hash(url)}", headless, url)

            result = {"url": url}
            if extract:
                try:
                    locator = connection.page.locator(extract)
                    elements = await locator.all()
                    extracted = []
                    for element in elements:
                        text_content = await element.text_content()
                        if text_content:
                            extracted.append(text_content.strip())
                    result["extracted"] = extracted if len(extracted) > 1 else (extracted[0] if extracted else "")
                except Exception as e:
                    result["error"] = str(e)
            else:
                result["title"] = await connection.page.title()

            return result

        # Process URLs in parallel with concurrency limit
        semaphore = asyncio.Semaphore(concurrency)

        async def process_with_semaphore(url):
            async with semaphore:
                return await process_url(url)

        with create_progress(f"Processing {len(urls)} URLs") as progress:
            task = progress.add_task("Scraping...", total=len(urls))
            tasks = [process_with_semaphore(url) for url in urls]
            for coro in asyncio.as_completed(tasks):
                result = await coro
                results.append(result)
                progress.update(task, advance=1)

        output_json(results)

    run_async(_batch_urls())


@app.command()
def selectors(
    selectors: str = typer.Argument(..., help='Comma-separated selectors (e.g., "h1,p,a")'),
    url: str = typer.Option(..., "--url", "-u", help="URL to navigate to"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Extract multiple selectors at once."""

    async def _batch_selectors():
        selector_list = [s.strip() for s in selectors.split(",")]

        connection = await get_connection(session_id, headless, url)

        results = {}
        for selector in selector_list:
            try:
                locator = connection.page.locator(selector)
                elements = await locator.all()
                extracted = []
                for element in elements:
                    text_content = await element.text_content()
                    if text_content:
                        extracted.append(text_content.strip())
                results[selector] = extracted if len(extracted) > 1 else (extracted[0] if extracted else "")
            except Exception as e:
                results[selector] = {"error": str(e)}

        output_json(results)

    run_async(_batch_selectors())


@app.command()
def script(
    file: str = typer.Argument(..., help="YAML or JSON script file"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Run commands from a script file."""
    import yaml

    async def _run_script():
        if not os.path.exists(file):
            output_json({"error": f"Script file not found: {file}"})
            return

        # Read script file
        with open(file, "r") as f:
            if file.endswith(".yaml") or file.endswith(".yml"):
                script_data = yaml.safe_load(f)
            elif file.endswith(".json"):
                script_data = json.load(f)
            else:
                output_json({"error": "Script file must be YAML or JSON"})
                return

        if "steps" not in script_data:
            output_json({"error": 'Script must contain a "steps" array'})
            return

        connection = await get_connection(session_id, headless)
        results = []

        for i, step in enumerate(script_data["steps"]):
            log_verbose(f"Executing step {i + 1}: {list(step.keys())[0]}")

            if "goto" in step:
                url = step["goto"]
                await connection.page.goto(url, wait_until="domcontentloaded", timeout=settings.timeout)
                results.append({"step": i + 1, "action": "goto", "url": url, "status": "success"})

            elif "extract" in step:
                extract_config = step["extract"]
                selector = extract_config.get("selector", "")
                output_file = extract_config.get("output")

                locator = connection.page.locator(selector)
                elements = await locator.all()
                extracted = []
                for element in elements:
                    text_content = await element.text_content()
                    if text_content:
                        extracted.append(text_content.strip())
                result_data = extracted if len(extracted) > 1 else (extracted[0] if extracted else "")

                if output_file:
                    with open(output_file, "w") as f:
                        json.dump(result_data, f, indent=2)

                results.append({"step": i + 1, "action": "extract", "selector": selector, "data": result_data})

            elif "click" in step:
                selector = step["click"]
                await connection.page.locator(selector).first.click()
                results.append({"step": i + 1, "action": "click", "selector": selector, "status": "success"})

            elif "type" in step:
                type_config = step["type"]
                selector = type_config.get("selector", "")
                text = type_config.get("text", "")
                await connection.page.locator(selector).first.fill(text)
                results.append({"step": i + 1, "action": "type", "selector": selector, "status": "success"})

            elif "wait" in step:
                wait_config = step["wait"]
                if "selector" in wait_config:
                    await connection.page.wait_for_selector(wait_config["selector"], timeout=settings.timeout)
                elif "timeout" in wait_config:
                    await connection.page.wait_for_timeout(wait_config["timeout"])
                results.append({"step": i + 1, "action": "wait", "status": "success"})

            elif "capture" in step:
                filename = step["capture"]
                await connection.page.screenshot(path=filename)
                results.append({"step": i + 1, "action": "capture", "filename": filename, "status": "success"})

            else:
                results.append(
                    {
                        "step": i + 1,
                        "action": "unknown",
                        "status": "error",
                        "error": f"Unknown action: {list(step.keys())[0]}",
                    }
                )

        output_json({"results": results, "status": "completed"})

    run_async(_run_script())


@app.command()
def retry(
    command: str = typer.Argument(..., help='Command to retry (e.g., "navigate goto https://example.com")'),
    max_attempts: int = typer.Option(3, help="Maximum number of retry attempts"),
    delay: int = typer.Option(1000, help="Delay between retries (ms)"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Auto-retry failed operations."""
    import subprocess

    async def _retry():
        for attempt in range(1, max_attempts + 1):
            log_verbose(f"Attempt {attempt}/{max_attempts}")

            try:
                # Execute command as subprocess
                result = subprocess.run(
                    command, shell=True, capture_output=True, text=True, timeout=settings.timeout / 1000
                )

                if result.returncode == 0:
                    output_json({"message": "Command succeeded", "attempt": attempt, "output": result.stdout})
                    return
                else:
                    if attempt < max_attempts:
                        log_verbose(f"Command failed, retrying in {delay}ms...")
                        await asyncio.sleep(delay / 1000)
                    else:
                        output_json(
                            {
                                "error": "Command failed after all retries",
                                "attempts": max_attempts,
                                "last_error": result.stderr,
                            }
                        )
            except subprocess.TimeoutExpired:
                if attempt < max_attempts:
                    log_verbose(f"Command timed out, retrying in {delay}ms...")
                    await asyncio.sleep(delay / 1000)
                else:
                    output_json({"error": "Command timed out after all retries", "attempts": max_attempts})
            except Exception as e:
                if attempt < max_attempts:
                    log_verbose(f"Error: {str(e)}, retrying in {delay}ms...")
                    await asyncio.sleep(delay / 1000)
                else:
                    output_json({"error": f"Command failed after all retries: {str(e)}", "attempts": max_attempts})

    run_async(_retry())
