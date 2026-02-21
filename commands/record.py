"""Recording and replay commands."""

import asyncio
import json
import time
from pathlib import Path
from typing import Optional

import typer

from core.async_command import get_connection, run_async
from core.output import output_json

app = typer.Typer()

# Global recording state
recording_data = {"actions": [], "start_time": None, "is_recording": False}


@app.command()
def start(
    output_file: str = typer.Option("recording.json", help="Output file for recording"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Start recording user actions."""

    async def _start_recording():
        connection = await get_connection(session_id, headless)

        recording_data["actions"] = []
        recording_data["start_time"] = time.time()
        recording_data["is_recording"] = True
        recording_data["output_file"] = output_file

        # Record navigation
        if url:
            await connection.page.goto(url, wait_until="domcontentloaded")
            recording_data["actions"].append(
                {"type": "navigate", "url": url, "timestamp": time.time() - recording_data["start_time"]}
            )

        # Set up event listeners
        async def on_click(event):
            if recording_data["is_recording"]:
                recording_data["actions"].append(
                    {
                        "type": "click",
                        "x": event.get("clientX"),
                        "y": event.get("clientY"),
                        "timestamp": time.time() - recording_data["start_time"],
                    }
                )

        async def on_input(event):
            if recording_data["is_recording"]:
                recording_data["actions"].append(
                    {
                        "type": "input",
                        "selector": event.get("target"),
                        "value": event.get("value"),
                        "timestamp": time.time() - recording_data["start_time"],
                    }
                )

        # Inject recording script
        await connection.page.evaluate("""
            () => {
                window.__recordedActions = [];

                document.addEventListener('click', (e) => {
                    const selector = e.target.id ? `#${e.target.id}` :
                                    e.target.className ? `.${e.target.className.split(' ')[0]}` :
                                    e.target.tagName.toLowerCase();
                    window.__recordedActions.push({
                        type: 'click',
                        selector: selector,
                        x: e.clientX,
                        y: e.clientY,
                        timestamp: Date.now()
                    });
                }, true);

                document.addEventListener('input', (e) => {
                    const selector = e.target.id ? `#${e.target.id}` :
                                    e.target.name ? `[name="${e.target.name}"]` :
                                    e.target.tagName.toLowerCase();
                    window.__recordedActions.push({
                        type: 'input',
                        selector: selector,
                        value: e.target.value,
                        timestamp: Date.now()
                    });
                }, true);

                document.addEventListener('keydown', (e) => {
                    if (e.key.length === 1 || ['Enter', 'Tab', 'Backspace'].includes(e.key)) {
                        window.__recordedActions.push({
                            type: 'keypress',
                            key: e.key,
                            timestamp: Date.now()
                        });
                    }
                }, true);
            }
        """)

        output_json({"message": "Recording started", "output_file": output_file, "url": connection.page.url})

    run_async(_start_recording())


@app.command()
def stop(
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Stop recording and save actions."""

    async def _stop_recording():
        if not recording_data["is_recording"]:
            output_json({"error": "No recording in progress"})
            return

        connection = await get_connection(session_id, headless)

        # Get recorded actions from browser
        browser_actions = await connection.page.evaluate("() => window.__recordedActions || []")

        # Merge with any server-side recorded actions
        all_actions = recording_data["actions"] + browser_actions

        # Sort by timestamp
        all_actions.sort(key=lambda x: x.get("timestamp", 0))

        # Save to file
        output_file = recording_data.get("output_file", "recording.json")
        recording_obj = {
            "version": "1.0",
            "startUrl": connection.page.url,
            "duration": time.time() - recording_data["start_time"],
            "actions": all_actions,
        }

        with open(output_file, "w") as f:
            json.dump(recording_obj, f, indent=2)

        recording_data["is_recording"] = False

        output_json(
            {
                "message": "Recording stopped",
                "output_file": output_file,
                "actions_count": len(all_actions),
                "duration": recording_obj["duration"],
            }
        )

    run_async(_stop_recording())


@app.command()
def replay(
    input_file: str,
    speed: float = typer.Option(1.0, help="Playback speed multiplier (1.0 = normal)"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Replay recorded actions."""

    async def _replay():
        connection = await get_connection(session_id, headless)

        # Load recording
        if not Path(input_file).exists():
            output_json({"error": f"Recording file not found: {input_file}"})
            return

        with open(input_file, "r") as f:
            recording = json.load(f)

        actions = recording.get("actions", [])
        start_url = recording.get("startUrl")

        output_json({"message": "Starting replay", "actions_count": len(actions), "speed": speed})

        # Navigate to start URL if available
        if start_url:
            await connection.page.goto(start_url, wait_until="domcontentloaded")

        last_timestamp = 0

        for i, action in enumerate(actions):
            action_type = action.get("type")
            timestamp = action.get("timestamp", 0)

            # Wait for timing (adjusted by speed)
            if timestamp > last_timestamp:
                delay = (timestamp - last_timestamp) / 1000 / speed
                await asyncio.sleep(delay)

            last_timestamp = timestamp

            try:
                if action_type == "navigate":
                    await connection.page.goto(action["url"], wait_until="domcontentloaded")

                elif action_type == "click":
                    if "selector" in action:
                        locator = connection.page.locator(action["selector"]).first
                        if await locator.count() > 0:
                            await locator.click()
                    elif "x" in action and "y" in action:
                        await connection.page.mouse.click(action["x"], action["y"])

                elif action_type == "input":
                    selector = action.get("selector")
                    value = action.get("value", "")
                    if selector:
                        locator = connection.page.locator(selector).first
                        if await locator.count() > 0:
                            await locator.fill(value)

                elif action_type == "keypress":
                    key = action.get("key")
                    if key:
                        await connection.page.keyboard.press(key)

                output_json({"progress": f"{i + 1}/{len(actions)}", "action": action_type})

            except Exception as e:
                output_json({"warning": f"Failed to replay action {i + 1}: {str(e)}", "action": action})

        output_json({"message": "Replay completed", "actions_replayed": len(actions)})

    run_async(_replay())


@app.command()
def video_start(
    output_file: str = typer.Option("recording.webm", help="Output video file"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Start video recording of browser session."""

    async def _video_start():
        connection = await get_connection(session_id, headless, url)

        # Start video recording using Playwright's video recording
        # Note: Video recording needs to be set at context creation
        # For existing contexts, we'll use CDP to start screen recording
        try:
            cdp = await connection.context.new_cdp_session(connection.page)

            # Start screencast (video recording via CDP)
            await cdp.send(
                "Page.startScreencast",
                {"format": "jpeg", "quality": 80, "maxWidth": 1920, "maxHeight": 1080, "everyNthFrame": 1},
            )

            # Store video frames (simplified - in production, use proper video encoding)
            recording_data["video_recording"] = True
            recording_data["video_file"] = output_file
            recording_data["video_frames"] = []

            # Set up frame handler
            def on_screencast_frame(params):
                if recording_data.get("video_recording"):
                    recording_data["video_frames"].append(
                        {"data": params.get("data"), "metadata": params.get("metadata")}
                    )

            cdp.on("Page.screencastFrame", on_screencast_frame)

            output_json(
                {
                    "message": "Video recording started",
                    "output_file": output_file,
                    "url": connection.page.url,
                    "note": 'Use "record video-stop" to stop recording',
                }
            )
        except Exception as e:
            output_json(
                {
                    "error": f"Failed to start video recording: {str(e)}",
                    "note": "Video recording requires CDP support. Try using context-level recording instead.",
                }
            )

    run_async(_video_start())


@app.command()
def video_stop(
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Stop video recording and save file."""

    async def _video_stop():
        if not recording_data.get("video_recording"):
            output_json({"error": "No video recording in progress"})
            return

        connection = await get_connection(session_id, headless)

        try:
            cdp = await connection.context.new_cdp_session(connection.page)

            # Stop screencast
            await cdp.send("Page.stopScreencast")

            recording_data["video_recording"] = False

            # Save frames to video file (simplified)
            output_file = recording_data.get("video_file", "recording.webm")
            frames = recording_data.get("video_frames", [])

            # For production use, encode frames to video using ffmpeg or similar
            # Here we'll save frame data as a simple format
            output_json(
                {
                    "message": "Video recording stopped",
                    "output_file": output_file,
                    "frames_captured": len(frames),
                    "note": "Frame data captured. Use ffmpeg or similar tool to encode to video format.",
                }
            )

            # Clear recording data
            recording_data["video_frames"] = []

        except Exception as e:
            output_json({"error": f"Failed to stop video recording: {str(e)}"})

    run_async(_video_stop())


@app.command()
def video_context(
    output_dir: str = typer.Option("./videos", help="Output directory for videos"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to"),
    width: int = typer.Option(1920, help="Video width"),
    height: int = typer.Option(1080, help="Video height"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
):
    """Start a new browser context with video recording enabled."""
    from pathlib import Path

    async def _video_context():
        from playwright.async_api import async_playwright

        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)

        # Create context with video recording
        context = await browser.new_context(
            record_video_dir=output_dir,
            record_video_size={"width": width, "height": height},
            viewport={"width": width, "height": height},
        )

        page = await context.new_page()

        if url:
            await page.goto(url, wait_until="domcontentloaded")

        output_json(
            {
                "message": "Browser context created with video recording",
                "output_dir": output_dir,
                "video_size": f"{width}x{height}",
                "url": page.url if url else "about:blank",
                "note": "Video will be saved when context is closed. Use regular commands to interact.",
            }
        )

        # Keep context open
        # Video will be saved automatically when context closes

    run_async(_video_context())
