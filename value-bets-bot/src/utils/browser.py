"""
browser.py
Playwright browser helpers: context creation, cookie-banner dismissal,
and page configuration.
"""
from __future__ import annotations

from playwright.async_api import Browser, BrowserContext, Page


_COOKIE_SELECTORS = [
    "button:has-text('Accept')",
    "button:has-text('Aceptar')",
    "button:has-text('Accept all')",
    "button:has-text('Accept All')",
    "#onetrust-accept-btn-handler",
    ".cookie-accept",
]


async def make_browser_context(pw, headless: bool) -> tuple[Browser, BrowserContext]:
    """Launch Chromium and return a configured browser + context pair."""
    browser = await pw.chromium.launch(
        headless=headless,
        args=["--no-sandbox", "--disable-dev-shm-usage"],
    )
    ctx = await browser.new_context(
        viewport={"width": 1280, "height": 900},
        user_agent=(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        locale="es-ES",
    )
    return browser, ctx


async def accept_cookies(page: Page) -> None:
    """Dismiss cookie banners if present."""
    for sel in _COOKIE_SELECTORS:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=1500):
                await btn.click()
                await page.wait_for_timeout(400)
                return
        except Exception:
            pass


async def configure_page(page: Page) -> None:
    """Block binary assets to reduce bandwidth and speed up page loads."""
    await page.route(
        "**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,mp4,webm}",
        lambda route: route.abort(),
    )
