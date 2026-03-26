"""
oddschecker.py
Scraping logic for Oddschecker: match page Bet365 corners Over/Under odds.

Bet365 Spain is identified by data-bk="HG" in the odds comparison grid.
The corners market lives under "Apuestas de estadísticas" → "Córners - Total"
→ "Comparar todas las cuotas".

Match URLs are built directly from Pinnacle team names to avoid Cloudflare
detection (navigating league page → match triggers bot detection).
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout, Error as PlaywrightError

from src.core.models import MatchOdds, OddsOU
from src.utils.browser import accept_cookies

log = logging.getLogger(__name__)

_CORNERS_LINES: list[str] = ["7.5", "8.5", "9.5", "10.5", "11.5"]
_BET365_BK     = "HG"
_MAX_RETRIES   = 2
_RETRY_WAIT    = 3.0


async def scrape_match(page: Page, match: dict) -> Optional[MatchOdds]:
    """
    Scrape Bet365 corners odds from an Oddschecker match page.

    Flow:
      1. Load the match page (URL pre-built from Pinnacle team names).
      2. Detect Cloudflare/404 via page title.
      3. Click "Apuestas de estadísticas".
      4. Verify "Córners - Total" is present.
      5. Click "Comparar todas las cuotas" to open the bookmaker grid.
      6. Extract Bet365 (data-bk="HG") over/under prices for lines 7.5–11.5.
    """
    log.info(f"[Oddschecker] Scraping {match['home']} vs {match['away']}")
    result = MatchOdds(
        competition=match.get("competition", ""),
        home_team=match["home"],
        away_team=match["away"],
        kickoff=match["kickoff"],
        source="oddschecker",
    )

    # ── 1. Load match page ────────────────────────────────────────────────────
    loaded = False
    for attempt in range(_MAX_RETRIES + 1):
        try:
            await page.goto(match["url"], wait_until="domcontentloaded", timeout=35_000)
            await page.wait_for_timeout(1500)  # allow React to mount tabs
            # Detect URL mismatch: Cloudflare/404 pages have no Oddschecker content
            page_title = await page.title()
            if any(k in page_title for k in ("Cloudflare", "404", "Not Found", "Page not found", "Error")):
                log.warning(
                    f"[Oddschecker] [{match['home']} vs {match['away']}] "
                    f"URL not found — team names may differ on Oddschecker. "
                    f"URL: {match['url']}"
                )
                return result
            loaded = True
            break
        except (PlaywrightTimeout, PlaywrightError):
            if attempt < _MAX_RETRIES:
                log.warning(
                    f"[Oddschecker] [{match['home']} vs {match['away']}] "
                    f"Error loading match page — retry {attempt + 1}/{_MAX_RETRIES}"
                )
                await asyncio.sleep(_RETRY_WAIT)
            else:
                log.warning(
                    f"[Oddschecker] [{match['home']} vs {match['away']}] "
                    f"Failed after {_MAX_RETRIES + 1} attempts — skipping"
                )

    if not loaded:
        return result

    await accept_cookies(page)

    # ── 2 & 3. Navigate to stats tab and verify corners market ───────────────
    if not await _find_corners_section(page):
        log.info(
            f"[Oddschecker] [{match['home']} vs {match['away']}] "
            "'Córners - Total' market not available"
        )
        return result

    # ── 4. Open comparison grid ───────────────────────────────────────────────
    if not await _open_compare_grid(page):
        log.warning(
            f"[Oddschecker] [{match['home']} vs {match['away']}] "
            "Could not open odds comparison grid"
        )
        return result

    # ── 5. Wait for grid rows ─────────────────────────────────────────────────
    try:
        await page.wait_for_selector('[data-testid="odds-row"]', timeout=8_000)
    except Exception:
        log.warning(
            f"[Oddschecker] [{match['home']} vs {match['away']}] "
            "Odds grid did not load in time"
        )
        return result

    # ── 6. Extract Bet365 prices ──────────────────────────────────────────────
    corners = await _extract_bet365_corners(page)
    if not corners:
        log.info(
            f"[Oddschecker] [{match['home']} vs {match['away']}] "
            "Bet365 corners odds not found"
        )
        return result

    for line, attr in [
        ("7.5",  "m_ou_corners_75"),
        ("8.5",  "m_ou_corners_85"),
        ("9.5",  "m_ou_corners_95"),
        ("10.5", "m_ou_corners_105"),
        ("11.5", "m_ou_corners_115"),
    ]:
        if line in corners:
            over, under = corners[line]
            setattr(result, attr, OddsOU(over=over, under=under))

    return result


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _find_corners_section(page: Page) -> bool:
    """
    Click "Apuestas de estadísticas" and confirm "Córners - Total" is present.
    Returns True if the market is available, False otherwise.
    """
    try:
        await page.wait_for_selector('[data-testid="filter-button"]', timeout=15_000)
    except Exception:
        log.warning("[Oddschecker] Market filter tabs did not appear — match may be live or page failed to load")
        return False

    try:
        stats_btn = (
            page.locator('[data-testid="filter-button"]')
            .filter(has_text="Apuestas de estadísticas")
            .first
        )
        if not await stats_btn.is_visible(timeout=5_000):
            log.warning("[Oddschecker] 'Apuestas de estadísticas' tab not found")
            return False
        await stats_btn.click()
    except Exception as e:
        log.warning(f"[Oddschecker] Error clicking stats tab: {e}")
        return False

    # Wait for React to render the stats tab content, then check for corners.
    # Two attempts with increasing waits handle slow network conditions.
    for wait_ms in (2000, 3000):
        await page.wait_for_timeout(wait_ms)
        try:
            headers = await page.evaluate("""() =>
                [...document.querySelectorAll('[data-testid="market-header"]')]
                .map(h => h.textContent.trim())
            """)
        except Exception as e:
            log.warning(f"[Oddschecker] Error reading market headers: {e}")
            return False
        if any('rners - Total' in h for h in headers):
            return True
    log.info("[Oddschecker] 'Córners - Total' not available for this match")
    return False


async def _open_compare_grid(page: Page) -> bool:
    """
    Click "Comparar todas las cuotas" to open the full bookmaker grid.
    Skips the click if already expanded.
    """
    try:
        btn = page.locator('[data-testid="compare-odds"]').first
        if not await btn.is_visible(timeout=5_000):
            log.warning("[Oddschecker] 'Comparar todas las cuotas' button not visible")
            return False
        if await btn.get_attribute("aria-expanded") != "true":
            await btn.click()
            await asyncio.sleep(1.5)
        return True
    except Exception as e:
        log.warning(f"[Oddschecker] Error opening comparison grid: {e}")
        return False


async def _extract_bet365_corners(page: Page) -> dict:
    """
    Extract Bet365 (data-bk="HG") over/under prices for corners lines 7.5–11.5
    from the virtualised odds grid.

    Returns: {"7.5": [over, under], "8.5": [over, under], ...}
    """
    try:
        await page.evaluate("""() => {
            for (const c of document.querySelectorAll('[id*="scrollable-container"]')) {
                c.scrollTop = 500;
            }
            const outer = document.querySelector('[class*="outerWrapper"]');
            if (outer) outer.scrollTop = 500;
        }""")
        await page.wait_for_timeout(600)
    except Exception:
        pass

    try:
        result = await page.evaluate(r"""() => {
            const TARGET_BK = "HG";
            const LINES     = ["7.5", "8.5", "9.5", "10.5", "11.5"];

            // 1. Find Bet365 column index
            const allBkLinks = document.querySelectorAll('a[data-bk]');
            const seenBk = new Set();
            let bet365Col = -1, idx = 0;
            for (const el of allBkLinks) {
                if (!seenBk.has(el.dataset.bk)) {
                    if (el.dataset.bk === TARGET_BK) { bet365Col = idx; break; }
                    seenBk.add(el.dataset.bk);
                    idx++;
                }
            }
            if (bet365Col === -1) return null;

            // 2. Bet names (always fully rendered in DOM)
            const betNames = [...document.querySelectorAll('[data-testid="grid-bet"]')]
                              .map(el => el.textContent.trim());

            // 3. Get Bet365 price from a rendered row by column position
            function getBet365Price(row) {
                let colIdx = 0;
                for (const child of row.children) {
                    if (child.querySelector('h4')) continue;
                    if ([...child.classList].some(c => c.includes('Margin'))) continue;
                    if (colIdx === bet365Col) {
                        const btn = child.querySelector('[data-testid="odds-cell"]');
                        return btn ? parseFloat(btn.textContent.trim()) : null;
                    }
                    colIdx++;
                }
                return null;
            }

            // 4. Match rows by translateY (each row = 54px height)
            const nameToIdx = {};
            betNames.forEach((bn, i) => { nameToIdx[bn] = i; });

            const oddsRows = [...document.querySelectorAll('[data-testid="odds-row"]')];
            const corners  = {};

            for (const line of LINES) {
                const overName  = "Más De "  + line;
                const underName = "Menos De " + line;
                const overIdx   = nameToIdx[overName]  ?? -1;
                const underIdx  = nameToIdx[underName] ?? -1;
                if (overIdx === -1 || underIdx === -1) continue;

                const overY  = overIdx  * 54;
                const underY = underIdx * 54;
                let overPrice = null, underPrice = null;

                for (const row of oddsRows) {
                    const parent = row.closest('[style*="translateY"]') || row.parentElement;
                    const style  = parent ? parent.style.transform : '';
                    const m = style && style.match(/translateY\((\d+)px\)/);
                    if (!m) continue;
                    const rowY = parseInt(m[1]);
                    if (rowY === overY)  overPrice  = getBet365Price(row);
                    if (rowY === underY) underPrice = getBet365Price(row);
                }

                if (overPrice && underPrice) {
                    corners[line] = [overPrice, underPrice];
                }
            }

            return Object.keys(corners).length > 0 ? corners : null;
        }""")
        return result or {}
    except Exception as e:
        log.warning(f"[Oddschecker] Error extracting corners odds: {e}")
        return {}
