"""
pinnacle.py
Scraping logic for Pinnacle: league page (today's matches) and match page (odds).
"""
from __future__ import annotations

import logging
import re
from datetime import date
from typing import Optional

from bs4 import BeautifulSoup
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout, Error as PlaywrightError

from src.core.models import MatchOdds, Odds1x2, OddsDC, OddsBTS, OddsDNB, OddsOU, HtFtSet
from src.utils.browser import accept_cookies
from src.utils.matching import _normalize
from src.utils.parsers import parse_float

log = logging.getLogger(__name__)

# ── Market section titles (Pinnacle Spanish UI) ───────────────────────────────
_TITLE_1X2   = "Línea de dinero \u2013 Partido"
_TITLE_DC    = "Doble Oportunidad"
_TITLE_BTS   = "¿Anotarán los dos equipos?"
_TITLE_TOTAL = "Total \u2013 Partido"
_TITLE_HTFT  = "Resultado al descanso/resultado final"
_TITLE_DNB     = "Empate no apuesta"
_TITLE_CORNERS = "Total (Córneres)Partido"
_OU_LINES      = ["1.5", "2.5", "3.5", "4.5"]
_CORNERS_LINES = ["7.5", "8.5", "9.5", "10.5", "11.5"]


# ── League page ───────────────────────────────────────────────────────────────

async def get_today_matches(page: Page, competition: str, url: str) -> list[dict]:
    """Return today's matches from a Pinnacle league page. Retries up to 3 times."""
    log.info(f"[Pinnacle] {competition}: {url}")
    for attempt in range(3):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=40_000)
        except (PlaywrightTimeout, PlaywrightError) as e:
            if attempt < 2:
                log.warning(f"[Pinnacle] [{competition}] Error cargando página de liga — reintento {attempt + 1}/2")
                import asyncio; await asyncio.sleep(3.0)
                continue
            log.warning(f"[Pinnacle] [{competition}] Error cargando página de liga tras 3 intentos — descartando")
            return []

        await accept_cookies(page)

        ceiling = 8000 + attempt * 3000
        try:
            await page.wait_for_selector(
                'div.contentBlock.square div[data-test-id="Events.DateBar"]',
                timeout=ceiling,
            )
        except Exception:
            await page.wait_for_timeout(ceiling)

        html = await page.content()

        if "contentBlock" in html:
            matches = _parse_today_matches(html, competition)
            if matches or attempt == 2:
                return matches
            log.warning(f"[Pinnacle] [{competition}] No se encontraron partidos — reintento {attempt + 1}/2")

    log.warning(f"[Pinnacle] [{competition}] Contenido de la página no encontrado tras 3 intentos — descartando")
    return []


def _parse_today_matches(html: str, competition: str) -> list[dict]:
    """
    Parse today's matches from the Pinnacle league page HTML.

    Pinnacle uses two rendering modes depending on the number of matches:

    A) Direct children (many matches — e.g. Premier League):
         div.contentBlock.square
           div.dateBar-*[data-test-id="Events.DateBar"]  ← "Hoy(N)"
           div.row-* (no link)                            ← column-header, skip
           div.row-* (has link)                           ← match row
           div.dateBar-*                                  ← next time-slot / date
           …

    B) Virtualized scrollable list (few matches — e.g. La Liga):
         div.contentBlock.square
           div.dateBar-*[data-test-id="Events.DateBar"]  ← "Hoy(N)"
           div#events-chunkmode                           ← scroll container
             div.list-* scrollbar
               div.scrollbar-item
                 div.row-* (no link)                     ← column-header, skip
                 div.row-* (has link)                    ← match row

    In both cases we only collect rows that fall under a "Hoy" DateBar.
    """
    today = date.today().isoformat()
    soup  = BeautifulSoup(html, "lxml")
    seen, matches = set(), []

    block = (
        soup.find("div", class_=lambda c: c and "contentBlock" in c and "square" in c)
        or soup.find("div", class_=lambda c: c and "contentBlock" in c)
    )
    if not block:
        log.warning("[Pinnacle] Estructura de la página no reconocida — no se pudo parsear")
        return []

    _match_href = re.compile(r'/es/soccer/[^/]+/[^/]+-vs-[^/]+/\d+')
    _special    = re.compile(r'home-teams|away-teams|over|under')
    _suffix     = re.compile(r'\s*\(Partido\)\s*$', re.IGNORECASE)

    def _extract_match(row, today: str) -> Optional[dict]:
        link = row.find("a", href=_match_href)
        if not link:
            return None
        href = link["href"]
        if href in seen:
            return None
        m = re.search(r'/es/soccer/[^/]+/([^/]+-vs-[^/]+)/\d+', href)
        if not m:
            return None
        home_slug, _, away_slug = m.group(1).partition("-vs-")
        if _special.search(home_slug):
            return None
        seen.add(href)

        labels = row.find_all("div", class_=re.compile(r"gameInfoLabel"))
        if len(labels) >= 2:
            home = _suffix.sub("", labels[0].get_text(strip=True))
            away = _suffix.sub("", labels[1].get_text(strip=True))
        else:
            home = home_slug.replace("-", " ").title()
            away = away_slug.replace("-", " ").title()

        time_el = row.find("div", class_=re.compile(r"matchupDate"))
        if time_el:
            t = time_el.get_text(strip=True)
            kickoff = f"{today}T{t}" if re.match(r'\d{2}:\d{2}', t) else today
        else:
            time_m = re.search(r'\b(\d{2}:\d{2})\b', row.get_text())
            kickoff = f"{today}T{time_m.group(1)}" if time_m else today

        return {
            "competition": competition,
            "home":    home,
            "away":    away,
            "kickoff": kickoff,
            "url":     f"https://www.pinnacle.com{href}".rstrip("/"),
        }

    in_today = False
    for child in block.children:
        if not hasattr(child, "get"):
            continue

        if child.get("data-test-id") == "Events.DateBar":
            in_today = "hoy" in child.get_text(strip=True).lower()
            continue

        if not in_today:
            continue

        if child.find("a", href=_match_href):
            match = _extract_match(child, today)
            if match:
                matches.append(match)
            continue

        for row in child.find_all("div", class_=re.compile(r"\brow-\w")):
            if not row.find("a", href=_match_href):
                continue
            match = _extract_match(row, today)
            if match:
                matches.append(match)

    log.info(f"[Pinnacle] {len(matches)} matches today in {competition}")
    return matches


# ── Match page ────────────────────────────────────────────────────────────────

async def scrape_match(page: Page, match: dict, markets: frozenset[str] | None = None) -> Optional[MatchOdds]:
    """Navigate to the Pinnacle match page and return scraped odds. Retries up to 2 times."""
    import asyncio
    url = match["url"] + "#all"
    log.info(f"[Pinnacle] Scraping {match['home']} vs {match['away']}")

    loaded = False
    for attempt in range(3):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=40_000)
            loaded = True
            break
        except (PlaywrightTimeout, PlaywrightError) as e:
            if attempt < 2:
                log.warning(
                    f"[Pinnacle] [{match['home']} vs {match['away']}] "
                    f"Error cargando página del partido — reintento {attempt + 1}/2"
                )
                await asyncio.sleep(3.0)
            else:
                log.warning(
                    f"[Pinnacle] [{match['home']} vs {match['away']}] "
                    f"Error cargando página del partido tras 3 intentos — descartando"
                )

    if not loaded:
        return None

    await accept_cookies(page)

    # Esperamos a que el bloque principal de mercados esté en el DOM antes de
    # intentar expandir o parsear. Reemplaza el wait_for_timeout(2500) fijo.
    try:
        await page.wait_for_selector(
            'div[class*="marketGroup"]', timeout=12_000
        )
    except Exception:
        log.warning(f"[Pinnacle] [{match['home']} vs {match['away']}] Mercados no cargaron a tiempo — intentando parsear igualmente")

    if markets is None or {"dc", "bts", "dnb", "ht_ft"} & markets:
        await _expand_markets(page, markets)
    if markets is None or "ou_goals" in markets:
        await _expand_total(page)
    if markets is None or "ou_corners" in (markets or set()):
        await _expand_corners(page)

    await page.wait_for_timeout(400 if (markets is None or "ou_goals" in markets) else 100)

    ou      = await _extract_ou(page)      if (markets is None or "ou_goals" in markets)                else {}
    corners = await _extract_corners(page) if (markets is None or "ou_corners" in (markets or set())) else {}
    result  = _parse_odds(await page.content(), match, markets)

    # Retry once if main market is empty (timing issue)
    if result and result.m_1x2.home is None and (markets is None or "1x2" in markets):
        log.warning(f"[Pinnacle] [{match['home']} vs {match['away']}] Mercados vacíos — reintentando lectura")
        try:
            await page.wait_for_selector(
                'div[class*="marketGroup"]', timeout=8_000
            )
        except Exception:
            pass
        if markets is None or {"dc", "bts", "dnb", "ht_ft"} & markets:
            await _expand_markets(page, markets)
        if markets is None or "ou_goals" in markets:
            await _expand_total(page)
        if markets is None or "ou_corners" in (markets or set()):
            await _expand_corners(page)
        await page.wait_for_timeout(400 if (markets is None or "ou_goals" in markets) else 100)
        ou      = await _extract_ou(page)      if (markets is None or "ou_goals" in markets)                else {}
        corners = await _extract_corners(page) if (markets is None or "ou_corners" in (markets or set())) else {}
        result  = _parse_odds(await page.content(), match, markets)

    if result and ou:
        for line_key, attr in [("1.5", "m_ou_goals_15"), ("2.5", "m_ou_goals_25"), ("3.5", "m_ou_goals_35"), ("4.5", "m_ou_goals_45")]:
            if ou.get(line_key):
                setattr(result, attr, OddsOU(over=ou[line_key][0], under=ou[line_key][1]))

    if result and corners:
        for line_key, attr in [
            ("7.5",  "m_ou_corners_75"),
            ("8.5",  "m_ou_corners_85"),
            ("9.5",  "m_ou_corners_95"),
            ("10.5", "m_ou_corners_105"),
            ("11.5", "m_ou_corners_115"),
        ]:
            if corners.get(line_key):
                setattr(result, attr, OddsOU(over=corners[line_key][0], under=corners[line_key][1]))

    return result


# ── Interaction helpers ───────────────────────────────────────────────────────

async def _expand_markets(page: Page, markets: frozenset[str] | None = None) -> None:
    """Expand DC, BTS and HT/FT sections if collapsed and requested."""
    targets = []
    if markets is None or "dc" in markets:
        targets.append(_TITLE_DC)
    if markets is None or "bts" in markets:
        targets.append(_TITLE_BTS)
    if markets is None or "ht_ft" in markets:
        targets.append(_TITLE_HTFT)
    if markets is None or "dnb" in markets:
        targets.append(_TITLE_DNB)
    for title in targets:
        try:
            xpath = (
                f'//span[contains(@class,"titleText") and normalize-space(text())="{title}"]'
                f'/ancestor::div[contains(@class,"collapseTitle") or contains(@class,"collapse-title")][1]'
            )
            el = page.locator(f'xpath={xpath}').first
            if await el.is_visible(timeout=2500):
                await el.click()
                await page.wait_for_timeout(600)
        except Exception:
            pass


async def _expand_total(page: Page) -> bool:
    """
    Expand the 'Total – Partido' group and click 'show more' to reveal all O/U lines.
    Falls back to a JS click if Playwright locators fail.
    """
    try:
        for i in range(await page.locator('div[class*="marketGroup"][data-collapsed="true"]').count()):
            el = page.locator('div[class*="marketGroup"][data-collapsed="true"]').nth(i)
            try:
                title = await el.locator('span[class*="titleText"]').first.inner_text(timeout=400)
                if title.strip() == _TITLE_TOTAL:
                    await el.locator('div[class*="collapseTitle"]').first.click()
                    await page.wait_for_timeout(700)
                    break
            except Exception:
                pass
    except Exception:
        pass

    clicked = False
    try:
        for i in range(await page.locator('div[class*="marketGroup"][data-collapsed="false"]').count()):
            el = page.locator('div[class*="marketGroup"][data-collapsed="false"]').nth(i)
            try:
                title = await el.locator('span[class*="titleText"]').first.inner_text(timeout=400)
            except Exception:
                continue
            if title.strip() != _TITLE_TOTAL:
                continue
            btn = el.locator('button[class*="button-VcnnvaBxJw"]').first
            if await btn.is_visible(timeout=1200):
                label = await btn.inner_text()
                if any(kw in label.lower() for kw in ["información", "more", "ver"]):
                    await btn.click()
                    await page.wait_for_timeout(2000)
                    clicked = True
            break
    except Exception:
        pass

    if not clicked:
        try:
            r = await page.evaluate(f"""() => {{
                for (const row of document.querySelectorAll('div[class*="marketGroup"]')) {{
                    const t = row.querySelector('span[class*="titleText"]');
                    if (!t || t.textContent.trim() !== '{_TITLE_TOTAL}') continue;
                    for (const btn of row.querySelectorAll('button')) {{
                        const txt = btn.textContent.trim().toLowerCase();
                        if (txt.includes('información') || txt.includes('more') || txt.includes('ver más')) {{
                            btn.click(); return 'clicked';
                        }}
                    }}
                    return 'found_no_btn';
                }}
                return 'not_found';
            }}""")
            if r == "clicked":
                await page.wait_for_timeout(2000)
                clicked = True
        except Exception:
            pass

    return clicked


async def _expand_corners(page) -> bool:
    """Expand 'Total (Córneres)Partido' and click 'Más información' to load all lines."""
    try:
        r = await page.evaluate("""() => {
            const TITLE = "Total (C\u00f3rneres)Partido";
            for (const row of document.querySelectorAll('div[class*="marketGroup"]')) {
                const t = row.querySelector('span[class*="titleText"]');
                if (!t || t.textContent.trim() !== TITLE) continue;
                if (row.dataset.collapsed === 'true') {
                    const btn = row.querySelector('div[class*="collapseTitle"]');
                    if (btn) { btn.click(); return 'expanded'; }
                }
                return 'already_open';
            }
            return 'not_found';
        }""")
        if r == "expanded":
            await page.wait_for_timeout(700)
        if r == "not_found":
            return False
    except Exception:
        pass
    try:
        r2 = await page.evaluate("""() => {
            const TITLE = "Total (C\u00f3rneres)Partido";
            for (const row of document.querySelectorAll('div[class*="marketGroup"]')) {
                const t = row.querySelector('span[class*="titleText"]');
                if (!t || t.textContent.trim() !== TITLE) continue;
                for (const btn of row.querySelectorAll('button')) {
                    const txt = btn.textContent.trim().toLowerCase();
                    if (txt.includes('información') || txt.includes('more') || txt.includes('ver más')) {
                        btn.click(); return 'clicked';
                    }
                }
                return 'no_btn';
            }
            return 'not_found';
        }""")
        if r2 == "clicked":
            await page.wait_for_timeout(2000)
    except Exception:
        pass
    return True


async def _extract_corners(page) -> dict:
    """
    Extract corners Over/Under prices for lines 7.5–11.5
    from the 'Total (Córneres)Partido' market group.
    Returns: {"7.5": [over, under], ...}
    """
    try:
        return await page.evaluate(r"""() => {
            const LINES = ["7.5", "8.5", "9.5", "10.5", "11.5"];
            const TITLE = "Total (Córneres)Partido";
            const res   = {};
            for (const row of document.querySelectorAll('div[class*="marketGroup"]')) {
                const t = row.querySelector('span[class*="titleText"]');
                if (!t || t.textContent.trim() !== TITLE) continue;
                if (!row.querySelectorAll('button[class*="market-btn"]').length) continue;
                for (const btn of row.querySelectorAll('button[class*="market-btn"]')) {
                    const lbl = btn.querySelector('span[class*="label"]');
                    const prc = btn.querySelector('span[class*="price"]');
                    if (!lbl || !prc) continue;
                    const price = parseFloat(prc.textContent.trim());
                    if (isNaN(price) || price <= 1.0) continue;
                    const m = lbl.textContent.trim().match(/^(M[aá]s|Menos)\s+de\s+(\d+\.\d+)\s+C/i);
                    if (!m) continue;
                    const line = m[2];
                    if (!LINES.includes(line)) continue;
                    const over = /más|mas/i.test(m[1]);
                    if (!res[line]) res[line] = [null, null];
                    if (over  && res[line][0] === null) res[line][0] = price;
                    if (!over && res[line][1] === null) res[line][1] = price;
                }
                break;
            }
            for (const k of Object.keys(res)) {
                if (res[k][0] === null || res[k][1] === null) delete res[k];
            }
            return res;
        }""") or {}
    except Exception:
        return {}



# ── Data extraction ───────────────────────────────────────────────────────────

async def _extract_ou(page: Page) -> dict:
    """
    Extract Over/Under prices for 1.5 / 2.5 / 3.5 / 4.5 from the live DOM,
    scoped strictly to the 'Total – Partido' market group.
    Returns: {"1.5": [over, under], …}
    """
    try:
        return await page.evaluate(f"""() => {{
            const LINES = ['1.5', '2.5', '3.5', '4.5'];
            const res = {{}};
            for (const row of document.querySelectorAll('div[class*="marketGroup"]')) {{
                const t = row.querySelector('span[class*="titleText"]');
                if (!t || t.textContent.trim() !== '{_TITLE_TOTAL}') continue;
                if (!row.querySelectorAll('button[class*="market-btn"]').length) continue;
                for (const btn of row.querySelectorAll('button[class*="market-btn"]')) {{
                    const lbl = btn.querySelector('span[class*="label"]');
                    const prc = btn.querySelector('span[class*="price"]');
                    if (!lbl || !prc) continue;
                    const price = parseFloat(prc.textContent.trim());
                    if (isNaN(price) || price <= 1.0) continue;
                    const m = lbl.textContent.trim().match(/^(M[aá]s|Menos)\\s+de\\s+(\\d+\\.5)$/i);
                    if (!m || !LINES.includes(m[2])) continue;
                    const line = m[2];
                    const over = /más|mas/i.test(m[1]);
                    if (!res[line]) res[line] = [null, null];
                    if (over  && res[line][0] === null) res[line][0] = price;
                    if (!over && res[line][1] === null) res[line][1] = price;
                }}
                break;
            }}
            for (const k of Object.keys(res)) {{
                if (res[k][0] === null || res[k][1] === null) delete res[k];
            }}
            return res;
        }}""") or {}
    except Exception:
        return {}


def _parse_odds(html: str, match: dict, markets: frozenset[str] | None = None) -> Optional[MatchOdds]:
    """Parse requested markets from Pinnacle match page HTML."""
    soup   = BeautifulSoup(html, "lxml")
    result = MatchOdds(
        competition=match.get("competition", ""),
        home_team=match["home"],
        away_team=match["away"],
        kickoff=match["kickoff"],
        source="pinnacle",
    )

    for mg in soup.find_all("div", attrs={"data-test-id": re.compile(r"^Event\.Row ")}):
        title_el = mg.find("span", class_=re.compile(r"titleText"))
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        btns  = _extract_buttons(mg)

        if title == _TITLE_1X2 and (markets is None or "1x2" in markets) and len(btns) >= 3:
            result.m_1x2 = Odds1x2(home=btns[0][1], draw=btns[1][1], away=btns[2][1])
        elif title == _TITLE_DC and (markets is None or "dc" in markets):
            result.m_dc = _parse_dc(btns, match)
        elif title == _TITLE_BTS and (markets is None or "bts" in markets):
            result.m_bts = _parse_bts(btns)
        elif title == _TITLE_DNB and (markets is None or "dnb" in markets):
            result.m_dnb = _parse_dnb(btns)
        elif title == _TITLE_HTFT and (markets is None or "ht_ft" in markets):
            result.m_ht_ft = _parse_ht_ft(btns, match)

    return result


def _extract_buttons(mg) -> list[tuple[str, float]]:
    """Extract (label, price) pairs from market-btn buttons."""
    result = []
    for btn in mg.find_all("button", class_=re.compile(r"market-btn")):
        label_el = btn.find("span", class_=re.compile(r"^label-"))
        label    = (label_el.get_text(strip=True) if label_el else None) or btn.get("title", "").strip()
        if not label:
            label = re.sub(r'\s+[\d.\-]+$', '', btn.get("aria-label", "")).strip()

        price_el = btn.find("span", class_=re.compile(r"^price-")) or next(
            (s for s in btn.find_all("span") if re.match(r'^\d+\.\d+$', s.get_text(strip=True))),
            None,
        )
        price = parse_float(price_el.get_text(strip=True)) if price_el else None
        if price:
            result.append((label, price))
    return result


def _parse_dc(btns: list, match: dict) -> OddsDC:
    """
    Assign DC button prices to h/d/a slots.
    Priority: numeric shortcuts (1X/12/X2) → keyword detection → positional fallback.
    """
    dc      = OddsDC()
    home_n  = _normalize(match["home"])
    away_n  = _normalize(match["away"])

    # Unique tokens: tokens present in home name but not in away, and vice versa.
    # This avoids false matches when both teams share words (e.g. 'Independiente').
    home_tokens = {t for t in home_n.split() if len(t) >= 3}
    away_tokens = {t for t in away_n.split() if len(t) >= 3}
    home_unique = home_tokens - away_tokens
    away_unique = away_tokens - home_tokens
    # Fall back to all tokens if there are no unique ones
    if not home_unique: home_unique = home_tokens
    if not away_unique: away_unique = away_tokens

    for label, price in btns:
        ln = _normalize(label)
        ll = label.lower()

        if ln == "1x": dc.home_draw = price; continue
        if ln == "12": dc.home_away = price; continue
        if ln == "x2": dc.draw_away = price; continue

        has_home = any(t in ln for t in home_unique)
        has_away = any(t in ln for t in away_unique)
        has_draw = any(k in ll for k in ["draw", "empate", "/x", "x/", " or draw", "draw or "])

        if   has_home and has_draw and not has_away: dc.home_draw = price
        elif has_draw and has_away and not has_home: dc.draw_away = price
        elif has_home and has_away and not has_draw: dc.home_away = price

    if dc.home_draw is None and dc.home_away is None and dc.draw_away is None and len(btns) >= 3:
        dc.home_draw, dc.home_away, dc.draw_away = btns[0][1], btns[1][1], btns[2][1]
    return dc


def _parse_bts(btns: list) -> OddsBTS:
    """Assign BTS button prices to yes/no."""
    bts = OddsBTS()
    for label, price in btns:
        ll = label.lower()
        if any(k in ll for k in ["sí", "si", "yes"]): bts.yes = price
        elif "no" in ll:                               bts.no = price
    if bts.yes is None and btns:           bts.yes = btns[0][1]
    if bts.no  is None and len(btns) >= 2: bts.no  = btns[1][1]
    return bts


def _parse_ht_ft(btns: list, match: dict) -> HtFtSet:
    """
    Assign HT/FT button prices to their slots.

    Pinnacle labels use real team names as separators, e.g.:
      'Barcelona - Barcelona'   → HT=home,  FT=home  → hh
      'Barcelona - Draw'        → HT=home,  FT=draw  → hd
      'Draw - Newcastle United' → HT=draw,  FT=away  → da

    Resolution order: exact 'Draw' keyword → home team tokens → away team tokens.
    """
    ht_ft  = HtFtSet()
    home_n = _normalize(match["home"])
    away_n = _normalize(match["away"])

    _MAP = {
        ("home", "home"): "hh", ("home", "draw"): "hd", ("home", "away"): "ha",
        ("draw", "home"): "dh", ("draw", "draw"): "dd", ("draw", "away"): "da",
        ("away", "home"): "ah", ("away", "draw"): "ad", ("away", "away"): "aa",
    }

    def _classify(token: str) -> Optional[str]:
        t = _normalize(token)
        if any(k in t for k in ("draw", "empate")):
            return "draw"
        if any(tok in t for tok in home_n.split() if len(tok) >= 3):
            return "home"
        if any(tok in t for tok in away_n.split() if len(tok) >= 3):
            return "away"
        return None

    for label, price in btns:
        # Labels: 'Team A - Draw', 'Draw - Team B', 'Team A - Team B', etc.
        parts = re.split(r"\s+-\s+", label.strip())
        if len(parts) == 2:
            ht = _classify(parts[0])
            ft = _classify(parts[1])
            if ht and ft:
                slot = _MAP.get((ht, ft))
                if slot:
                    setattr(ht_ft, slot, price)
            else:
                log.debug(f"[Pinnacle] Descanso/Resultado final: outcome no clasificado '{label}' (ht={ht}, ft={ft})")

    return ht_ft

def _parse_dnb(btns: list) -> OddsDNB:
    """Assign DNB button prices to home/away positionally."""
    dnb = OddsDNB()
    if btns:           dnb.home = btns[0][1]
    if len(btns) >= 2: dnb.away = btns[1][1]
    return dnb
