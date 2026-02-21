"""Element inspection commands."""

import json
from typing import Optional

import typer

from core.async_command import get_connection, run_async
from core.output import output_json

app = typer.Typer()


@app.command()
def styles(
    selector: str,
    properties: Optional[str] = typer.Option(None, help="Comma-separated CSS properties to get"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Get computed CSS styles for an element."""

    async def _styles():
        connection = await get_connection(session_id, headless, url)

        locator = connection.page.locator(selector).first
        if await locator.count() == 0:
            output_json({"error": f"Element not found: {selector}"})
            return

        # Get computed styles
        props_list = properties.split(",") if properties else None
        styles_data = await connection.page.evaluate(f"""
            () => {{
                const element = document.querySelector({json.dumps(selector)});
                if (!element) return null;

                const computed = window.getComputedStyle(element);
                const props = {json.dumps(props_list)};

                if (props) {{
                    const result = {{}};
                    props.forEach(prop => {{
                        result[prop.trim()] = computed.getPropertyValue(prop.trim());
                    }});
                    return result;
                }} else {{
                    // Return all styles
                    const result = {{}};
                    for (let i = 0; i < computed.length; i++) {{
                        const prop = computed[i];
                        result[prop] = computed.getPropertyValue(prop);
                    }}
                    return result;
                }}
            }}
        """)

        output_json({"selector": selector, "styles": styles_data})

    run_async(_styles())


@app.command()
def bounds(
    selector: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Get element bounding box (position and dimensions)."""

    async def _bounds():
        connection = await get_connection(session_id, headless, url)

        locator = connection.page.locator(selector).first
        if await locator.count() == 0:
            output_json({"error": f"Element not found: {selector}"})
            return

        box = await locator.bounding_box()

        if box:
            output_json(
                {
                    "selector": selector,
                    "bounds": {"x": box["x"], "y": box["y"], "width": box["width"], "height": box["height"]},
                }
            )
        else:
            output_json({"error": "Element has no bounding box (might be hidden)"})

    run_async(_bounds())


@app.command()
def contrast(
    selector: str,
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """Calculate color contrast ratio for WCAG compliance."""

    async def _contrast():
        connection = await get_connection(session_id, headless, url)

        locator = connection.page.locator(selector).first
        if await locator.count() == 0:
            output_json({"error": f"Element not found: {selector}"})
            return

        # Get colors and calculate contrast
        contrast_data = await connection.page.evaluate(f"""
            () => {{
                const element = document.querySelector({json.dumps(selector)});
                if (!element) return null;

                const computed = window.getComputedStyle(element);
                const color = computed.color;
                const backgroundColor = computed.backgroundColor;

                // Parse RGB values
                const parseRGB = (rgb) => {{
                    const match = rgb.match(/\\d+/g);
                    return match ? match.map(Number) : [0, 0, 0];
                }};

                const [r1, g1, b1] = parseRGB(color);
                const [r2, g2, b2] = parseRGB(backgroundColor);

                // Calculate relative luminance
                const luminance = (r, g, b) => {{
                    const [rs, gs, bs] = [r, g, b].map(c => {{
                        c = c / 255;
                        return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
                    }});
                    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
                }};

                const l1 = luminance(r1, g1, b1);
                const l2 = luminance(r2, g2, b2);

                // Calculate contrast ratio
                const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);

                return {{
                    color: color,
                    backgroundColor: backgroundColor,
                    contrastRatio: ratio.toFixed(2),
                    wcagAA: ratio >= 4.5,
                    wcagAAA: ratio >= 7,
                    wcagAALarge: ratio >= 3,
                    wcagAAALarge: ratio >= 4.5
                }};
            }}
        """)

        output_json({"selector": selector, "contrast": contrast_data})

    run_async(_contrast())


@app.command()
def fonts(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """List all fonts used on the page."""

    async def _fonts():
        connection = await get_connection(session_id, headless, url)

        fonts_data = await connection.page.evaluate("""
            () => {
                const elements = document.querySelectorAll('*');
                const fonts = new Set();

                elements.forEach(el => {
                    const computed = window.getComputedStyle(el);
                    const fontFamily = computed.fontFamily;
                    if (fontFamily) {
                        fonts.add(fontFamily);
                    }
                });

                // Get web fonts from CSS
                const webFonts = [];
                try {
                    for (const sheet of document.styleSheets) {
                        for (const rule of sheet.cssRules || sheet.rules) {
                            if (rule instanceof CSSFontFaceRule) {
                                webFonts.push({
                                    family: rule.style.fontFamily,
                                    src: rule.style.src,
                                    weight: rule.style.fontWeight,
                                    style: rule.style.fontStyle
                                });
                            }
                        }
                    }
                } catch (e) {
                    // Cross-origin stylesheets
                }

                return {
                    usedFonts: Array.from(fonts),
                    webFonts: webFonts
                };
            }
        """)

        output_json({"fonts": fonts_data, "url": connection.page.url})

    run_async(_fonts())


@app.command()
def sw(
    url: Optional[str] = typer.Option(None, "--url", "-u", help="URL to navigate to"),
    session_id: Optional[str] = typer.Option(None, help="Session ID to use"),
    headless: Optional[bool] = typer.Option(None, "--headless/--headed", help="Run in headless mode"),
):
    """List service workers."""

    async def _sw():
        connection = await get_connection(session_id, headless, url)

        sw_data = await connection.page.evaluate("""
            async () => {
                if (!navigator.serviceWorker) {
                    return { supported: false };
                }

                try {
                    const registrations = await navigator.serviceWorker.getRegistrations();
                    return {
                        supported: true,
                        registrations: registrations.map(reg => ({
                            scope: reg.scope,
                            active: reg.active ? {
                                scriptURL: reg.active.scriptURL,
                                state: reg.active.state
                            } : null,
                            waiting: reg.waiting ? {
                                scriptURL: reg.waiting.scriptURL,
                                state: reg.waiting.state
                            } : null,
                            installing: reg.installing ? {
                                scriptURL: reg.installing.scriptURL,
                                state: reg.installing.state
                            } : null
                        }))
                    };
                } catch (e) {
                    return { supported: true, error: e.message };
                }
            }
        """)

        output_json({"serviceWorkers": sw_data, "url": connection.page.url})

    run_async(_sw())
