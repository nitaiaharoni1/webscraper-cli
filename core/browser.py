"""Browser management for Playwright connections."""

from typing import Optional, Dict, Literal, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import os
import platform
import subprocess
import time
import socket


BrowserMode = Literal['fresh', 'cdp', 'profile', 'persistent']

# File to store persistent browser port
BROWSER_PORT_FILE = os.path.expanduser('~/.webscraper-browser-port')


def find_free_port() -> int:
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def get_chrome_path() -> Optional[str]:
    """Get the path to Chrome executable."""
    system = platform.system()
    
    if system == 'Darwin':  # macOS
        paths = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Chromium.app/Contents/MacOS/Chromium',
        ]
    elif system == 'Windows':
        paths = [
            os.path.expandvars(r'%ProgramFiles%\Google\Chrome\Application\chrome.exe'),
            os.path.expandvars(r'%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe'),
            os.path.expandvars(r'%LocalAppData%\Google\Chrome\Application\chrome.exe'),
        ]
    else:  # Linux
        paths = [
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium',
        ]
    
    for path in paths:
        if os.path.exists(path):
            return path
    return None


class BrowserConnection:
    """Represents an active browser connection."""

    def __init__(
        self,
        browser: Optional[Browser],
        context: BrowserContext,
        page: Page,
        mode: BrowserMode,
        session_id: str,
        process: Optional[subprocess.Popen] = None,
    ):
        self.browser = browser
        self.context = context
        self.page = page
        self.mode = mode
        self.session_id = session_id
        self.process = process  # Browser process for persistent mode

    async def close(self):
        """Close the browser connection."""
        if self.mode == 'persistent':
            # For persistent mode, just disconnect - don't close browser
            pass
        elif self.mode == 'profile':
            await self.context.close()
        elif self.browser:
            await self.browser.close()


class BrowserManager:
    """Manages browser connections."""

    def __init__(self):
        self.connections: Dict[str, BrowserConnection] = {}
        self._playwright = None
        self._persistent_process: Optional[subprocess.Popen] = None
        self._persistent_port: Optional[int] = None

    async def _get_playwright(self):
        """Get or create playwright instance."""
        if self._playwright is None:
            self._playwright = await async_playwright().start()
        return self._playwright

    def _check_existing_browser(self) -> Optional[int]:
        """Check if there's already a browser running from a previous session."""
        if os.path.exists(BROWSER_PORT_FILE):
            try:
                with open(BROWSER_PORT_FILE, 'r') as f:
                    port = int(f.read().strip())
                # Check if port is actually in use
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(('localhost', port))
                    if result == 0:
                        return port
            except Exception:
                pass
            # Clean up stale file
            try:
                os.remove(BROWSER_PORT_FILE)
            except Exception:
                pass
        return None

    def _launch_persistent_browser(self, headless: bool = False) -> int:
        """Launch a browser with remote debugging that stays open."""
        # First check if there's already a browser running
        existing_port = self._check_existing_browser()
        if existing_port:
            self._persistent_port = existing_port
            return existing_port
        
        if self._persistent_process and self._persistent_process.poll() is None:
            # Browser already running in this session
            return self._persistent_port
        
        chrome_path = get_chrome_path()
        if not chrome_path:
            raise RuntimeError('Chrome not found. Please install Chrome or Chromium.')
        
        port = find_free_port()
        
        # Create a temporary user data dir to avoid profile picker
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix='playwright_chrome_')
        
        args = [
            chrome_path,
            f'--remote-debugging-port={port}',
            f'--user-data-dir={temp_dir}',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-popup-blocking',
            '--disable-translate',
            '--disable-extensions',
            '--disable-background-networking',
            '--disable-sync',
            '--disable-default-apps',
            '--mute-audio',
            '--hide-scrollbars',
        ]
        
        if headless:
            args.append('--headless=new')
        
        self._temp_user_data_dir = temp_dir
        
        # Save port to file so other processes can reuse
        with open(BROWSER_PORT_FILE, 'w') as f:
            f.write(str(port))
        
        # Launch browser as separate process
        self._persistent_process = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._persistent_port = port
        
        # Wait for browser to start and port to be available
        for _ in range(20):
            time.sleep(0.5)
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(('localhost', port))
                    if result == 0:
                        break
            except Exception:
                pass
        
        return port

    async def connect(
        self,
        mode: BrowserMode = 'fresh',
        headless: bool = False,
        cdp_endpoint: Optional[str] = None,
        user_data_dir: Optional[str] = None,
        channel: Optional[str] = None,
        executable_path: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> BrowserConnection:
        """Connect to or launch a browser."""
        pw = await self._get_playwright()
        effective_session_id = session_id or f'session-{id(self)}'

        browser: Optional[Browser] = None
        context: BrowserContext
        process: Optional[subprocess.Popen] = None

        if mode == 'persistent':
            # Launch browser separately so it stays open
            port = self._launch_persistent_browser(headless=headless)
            cdp_url = f'http://localhost:{port}'
            
            # Wait and retry connection
            import asyncio as aio
            for attempt in range(20):
                try:
                    browser = await pw.chromium.connect_over_cdp(cdp_url)
                    break
                except Exception as e:
                    if attempt < 19:
                        await aio.sleep(0.5)
                    else:
                        raise RuntimeError(f'Could not connect to browser at {cdp_url}: {e}')
            
            contexts = browser.contexts
            context = contexts[0] if contexts else await browser.new_context()
            process = self._persistent_process

        elif mode == 'cdp':
            if not cdp_endpoint:
                raise ValueError('CDP endpoint is required for CDP mode')
            browser = await pw.chromium.connect_over_cdp(cdp_endpoint)
            contexts = browser.contexts
            context = contexts[0] if contexts else await browser.new_context()

        elif mode == 'profile':
            if not user_data_dir:
                raise ValueError('User data directory is required for profile mode')
            launch_options = {
                'headless': headless,
                'channel': channel or 'chrome',
            }
            if executable_path:
                launch_options['executable_path'] = executable_path
            context = await pw.chromium.launch_persistent_context(
                user_data_dir, **launch_options
            )
            browser = context.browser

        else:  # fresh
            browser_type = pw.chromium
            if channel == 'firefox':
                browser_type = pw.firefox
            elif channel == 'webkit':
                browser_type = pw.webkit

            launch_options = {
                'headless': headless,
            }
            if channel == 'chrome':
                launch_options['channel'] = 'chrome'
            if executable_path:
                launch_options['executable_path'] = executable_path

            # Fallback to system Chrome on macOS if no executable path specified
            if not executable_path and platform.system() == 'Darwin':
                system_chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
                if os.path.exists(system_chrome):
                    launch_options['executable_path'] = system_chrome

            browser = await browser_type.launch(**launch_options)
            context = await browser.new_context()

        # Get or create page
        pages = context.pages
        page = pages[0] if pages else await context.new_page()

        connection = BrowserConnection(browser, context, page, mode, effective_session_id, process)
        self.connections[effective_session_id] = connection
        return connection

    def get_connection(self, session_id: str) -> Optional[BrowserConnection]:
        """Get an existing connection by session ID."""
        return self.connections.get(session_id)

    async def close_connection(self, session_id: str):
        """Close a specific connection."""
        connection = self.connections.get(session_id)
        if connection:
            await connection.close()
            if session_id in self.connections:
                del self.connections[session_id]

    async def create_parallel_pages(self, count: int, session_id: str, headless: bool = False) -> List[Page]:
        """Create multiple pages in parallel for concurrent operations."""
        connection = await self.connect(
            mode='fresh',
            headless=headless,
            session_id=session_id,
        )
        pages = []
        for i in range(count - 1):  # -1 because connection already has one page
            page = await connection.context.new_page()
            pages.append(page)
        pages.insert(0, connection.page)  # Add the original page first
        return pages

    async def close_all(self):
        """Close all connections."""
        for connection in list(self.connections.values()):
            await connection.close()
        self.connections.clear()
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None


# Global browser manager instance
_browser_manager: Optional[BrowserManager] = None


def get_browser_manager() -> BrowserManager:
    """Get the global browser manager instance."""
    global _browser_manager
    if _browser_manager is None:
        _browser_manager = BrowserManager()
    return _browser_manager


async def get_or_create_connection(
    session_id: Optional[str] = None,
    headless: bool = False,
) -> BrowserConnection:
    """Get existing connection or create a new one."""
    bm = get_browser_manager()
    effective_session_id = session_id or 'default'

    # Check for existing connection
    connection = bm.get_connection(effective_session_id)
    if connection:
        return connection

    # Use persistent mode for headed, fresh for headless
    mode = 'fresh' if headless else 'persistent'
    
    connection = await bm.connect(
        mode=mode,
        headless=headless,
        session_id=effective_session_id,
    )
    return connection
