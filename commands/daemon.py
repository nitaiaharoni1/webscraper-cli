"""Daemon mode for persistent browser sessions."""

import typer
import json
import asyncio
import os
import signal
from typing import Optional
from core.browser import get_browser_manager
from core import settings

app = typer.Typer()

# PID file location
PID_FILE = os.path.expanduser('~/.webscraper-daemon.pid')
PORT_FILE = os.path.expanduser('~/.webscraper-daemon-port.json')


def output_json(data: dict):
    """Output JSON data."""
    if not settings.quiet:
        print(json.dumps(data, indent=2))


def save_pid(pid: int, port: int):
    """Save daemon PID and port."""
    with open(PID_FILE, 'w') as f:
        f.write(str(pid))
    with open(PORT_FILE, 'w') as f:
        json.dump({'port': port, 'pid': pid}, f)


def load_daemon_info():
    """Load daemon PID and port."""
    try:
        if os.path.exists(PORT_FILE):
            with open(PORT_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return None


def is_running(pid: int) -> bool:
    """Check if process is running."""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


@app.command()
def start(
    port: int = typer.Option(9222, '--port', '-p', help='CDP port for browser'),
    headless: bool = typer.Option(True, '--headless/--headed', help='Run browser in headless mode'),
):
    """Start daemon mode (persistent browser)."""
    import asyncio
    from playwright.async_api import async_playwright

    async def _start_daemon():
        # Check if already running
        daemon_info = load_daemon_info()
        if daemon_info and is_running(daemon_info.get('pid', 0)):
            output_json({'error': f'Daemon already running on port {daemon_info.get("port")}'})
            return

        pw = await async_playwright().start()
        browser = await pw.chromium.launch(
            headless=headless,
            args=[f'--remote-debugging-port={port}'],
        )

        # Save PID and port
        save_pid(os.getpid(), port)

        output_json({
            'message': 'Daemon started',
            'port': port,
            'pid': os.getpid(),
            'cdp_endpoint': f'http://localhost:{port}',
        })

        # Keep running
        try:
            await asyncio.Event().wait()  # Wait forever
        except KeyboardInterrupt:
            await browser.close()
            await pw.stop()
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
            if os.path.exists(PORT_FILE):
                os.remove(PORT_FILE)

    asyncio.run(_start_daemon())


@app.command()
def stop():
    """Stop daemon mode."""
    daemon_info = load_daemon_info()
    if not daemon_info:
        output_json({'error': 'Daemon not running'})
        return

    pid = daemon_info.get('pid')
    if pid and is_running(pid):
        try:
            os.kill(pid, signal.SIGTERM)
            output_json({'message': 'Daemon stopped'})
        except Exception as e:
            output_json({'error': f'Failed to stop daemon: {e}'})
    else:
        output_json({'error': 'Daemon process not found'})
        # Clean up stale files
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        if os.path.exists(PORT_FILE):
            os.remove(PORT_FILE)


@app.command()
def status():
    """Check daemon status."""
    daemon_info = load_daemon_info()
    if not daemon_info:
        output_json({'status': 'stopped'})
        return

    pid = daemon_info.get('pid')
    port = daemon_info.get('port')
    
    if pid and is_running(pid):
        output_json({
            'status': 'running',
            'pid': pid,
            'port': port,
            'cdp_endpoint': f'http://localhost:{port}',
        })
    else:
        output_json({'status': 'stopped', 'note': 'PID file exists but process not running'})


@app.command()
def connect(
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
):
    """Connect to running daemon."""
    daemon_info = load_daemon_info()
    if not daemon_info:
        output_json({'error': 'Daemon not running. Start it with: daemon start'})
        return

    port = daemon_info.get('port', 9222)
    cdp_endpoint = f'http://localhost:{port}'

    import asyncio
    from core.browser import get_browser_manager

    async def _connect():
        bm = get_browser_manager()
        connection = await bm.connect(
            mode='cdp',
            cdp_endpoint=cdp_endpoint,
            session_id=session_id or 'daemon',
        )
        output_json({
            'message': 'Connected to daemon',
            'cdp_endpoint': cdp_endpoint,
            'session_id': connection.session_id,
        })

    asyncio.run(_connect())
