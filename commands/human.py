"""Human-like interaction commands."""

import typer
import json
import random
import asyncio
from typing import Optional
from core.browser import get_or_create_connection
from core.settings import settings

app = typer.Typer()


def output_result(data):
    """Output data in the configured format."""
    if settings.format == 'json':
        print(json.dumps(data, indent=2))
    else:
        print(data)


@app.command()
def type(
    selector: str,
    text: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    min_delay: int = typer.Option(50, help='Minimum delay between keystrokes (ms)'),
    max_delay: int = typer.Option(150, help='Maximum delay between keystrokes (ms)'),
    typo_chance: float = typer.Option(0.02, help='Chance of typo (0-1)'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Type text with human-like delays and occasional typos."""
    async def _human_type():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')
        
        locator = connection.page.locator(selector).first
        if await locator.count() == 0:
            output_result({'error': f'Element not found: {selector}'})
            return
        
        await locator.click()
        
        # Type with human-like behavior
        typed_text = ''
        for i, char in enumerate(text):
            # Random chance of typo
            if random.random() < typo_chance and char.isalpha():
                # Type wrong character
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                await connection.page.keyboard.type(wrong_char)
                await asyncio.sleep(random.uniform(0.1, 0.3))
                # Backspace to correct
                await connection.page.keyboard.press('Backspace')
                await asyncio.sleep(random.uniform(0.05, 0.15))
            
            # Type correct character
            await connection.page.keyboard.type(char)
            typed_text += char
            
            # Random delay between keystrokes
            delay = random.uniform(min_delay / 1000, max_delay / 1000)
            
            # Longer pauses at word boundaries
            if char == ' ':
                delay *= random.uniform(1.5, 2.5)
            
            # Occasional thinking pauses
            if random.random() < 0.05:
                delay *= random.uniform(2, 4)
            
            await asyncio.sleep(delay)
        
        output_result({
            'message': f'Typed text with human-like behavior',
            'selector': selector,
            'length': len(text)
        })

    asyncio.run(_human_type())


@app.command()
def mouse(
    selector: str,
    action: str = typer.Option('click', help='Action: click, hover, dblclick'),
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Move mouse with realistic bezier curve and perform action."""
    async def _human_mouse():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')
        
        locator = connection.page.locator(selector).first
        if await locator.count() == 0:
            output_result({'error': f'Element not found: {selector}'})
            return
        
        # Get element position
        box = await locator.bounding_box()
        if not box:
            output_result({'error': 'Element has no bounding box'})
            return
        
        target_x = box['x'] + box['width'] / 2
        target_y = box['y'] + box['height'] / 2
        
        # Get current mouse position (start from 0,0 for simplicity)
        start_x, start_y = 0, 0
        
        # Generate bezier curve points for realistic movement
        steps = random.randint(20, 40)
        
        # Control points for bezier curve
        cp1_x = start_x + (target_x - start_x) * random.uniform(0.2, 0.4)
        cp1_y = start_y + (target_y - start_y) * random.uniform(-0.2, 0.5)
        cp2_x = start_x + (target_x - start_x) * random.uniform(0.6, 0.8)
        cp2_y = start_y + (target_y - start_y) * random.uniform(0.5, 1.2)
        
        # Move mouse along curve
        for i in range(steps):
            t = i / steps
            
            # Cubic bezier formula
            x = (1-t)**3 * start_x + 3*(1-t)**2*t * cp1_x + 3*(1-t)*t**2 * cp2_x + t**3 * target_x
            y = (1-t)**3 * start_y + 3*(1-t)**2*t * cp1_y + 3*(1-t)*t**2 * cp2_y + t**3 * target_y
            
            # Add small random jitter
            x += random.uniform(-2, 2)
            y += random.uniform(-2, 2)
            
            await connection.page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.005, 0.015))
        
        # Final move to exact position
        await connection.page.mouse.move(target_x, target_y)
        
        # Small pause before action (hover effect)
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        # Perform action
        if action == 'click':
            await connection.page.mouse.click(target_x, target_y)
        elif action == 'dblclick':
            await connection.page.mouse.dblclick(target_x, target_y)
        elif action == 'hover':
            pass  # Already hovering
        
        output_result({
            'message': f'Performed {action} with human-like mouse movement',
            'selector': selector,
            'position': {'x': target_x, 'y': target_y}
        })

    asyncio.run(_human_mouse())


@app.command()
def drag(
    source: str,
    target: str,
    url: Optional[str] = typer.Option(None, '--url', '-u', help='URL to navigate to'),
    session_id: Optional[str] = typer.Option(None, help='Session ID to use'),
    headless: bool = typer.Option(False, '--headless/--headed', help='Run in headless mode'),
):
    """Drag element from source to target with realistic timing."""
    async def _human_drag():
        connection = await get_or_create_connection(session_id, headless=headless)
        
        if url:
            await connection.page.goto(url, wait_until='domcontentloaded')
        
        source_locator = connection.page.locator(source).first
        target_locator = connection.page.locator(target).first
        
        if await source_locator.count() == 0:
            output_result({'error': f'Source element not found: {source}'})
            return
        
        if await target_locator.count() == 0:
            output_result({'error': f'Target element not found: {target}'})
            return
        
        # Get positions
        source_box = await source_locator.bounding_box()
        target_box = await target_locator.bounding_box()
        
        if not source_box or not target_box:
            output_result({'error': 'Element has no bounding box'})
            return
        
        # Perform drag with realistic timing
        source_x = source_box['x'] + source_box['width'] / 2
        source_y = source_box['y'] + source_box['height'] / 2
        target_x = target_box['x'] + target_box['width'] / 2
        target_y = target_box['y'] + target_box['height'] / 2
        
        # Move to source
        await connection.page.mouse.move(source_x, source_y)
        await asyncio.sleep(random.uniform(0.1, 0.2))
        
        # Press mouse down
        await connection.page.mouse.down()
        await asyncio.sleep(random.uniform(0.05, 0.1))
        
        # Drag to target with steps
        steps = random.randint(15, 30)
        for i in range(1, steps + 1):
            t = i / steps
            x = source_x + (target_x - source_x) * t
            y = source_y + (target_y - source_y) * t
            
            # Add jitter
            x += random.uniform(-1, 1)
            y += random.uniform(-1, 1)
            
            await connection.page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.01, 0.03))
        
        # Release mouse
        await asyncio.sleep(random.uniform(0.05, 0.15))
        await connection.page.mouse.up()
        
        output_result({
            'message': 'Dragged element with human-like movement',
            'source': source,
            'target': target
        })

    asyncio.run(_human_drag())
