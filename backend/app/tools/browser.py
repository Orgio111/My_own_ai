"""Browser tool — Playwright headless automation (lazy-imported)."""
from __future__ import annotations

from typing import Optional

from app.agents.executor import register_tool

_browser = None
_page = None


async def _ensure_page():
    global _browser, _page
    if _page is not None:
        return _page
    from playwright.async_api import async_playwright  # lazy

    pw = await async_playwright().start()
    _browser = await pw.chromium.launch(headless=True)
    ctx = await _browser.new_context()
    _page = await ctx.new_page()
    return _page


async def open_url(url: str) -> str:
    page = await _ensure_page()
    await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
    return f"opened {url}"


async def read_page(selector: Optional[str] = None) -> str:
    page = await _ensure_page()
    if selector:
        return (await page.locator(selector).inner_text())[:20_000]
    return (await page.inner_text("body"))[:20_000]


async def click(selector: str) -> str:
    page = await _ensure_page()
    await page.locator(selector).click()
    return f"clicked {selector}"


async def submit(selector: str, value: str) -> str:
    page = await _ensure_page()
    await page.locator(selector).fill(value)
    await page.keyboard.press("Enter")
    return f"submitted {selector}"


register_tool("browser.open", open_url)
register_tool("browser.read", read_page)
register_tool("browser.click", click)
register_tool("browser.submit", submit)
