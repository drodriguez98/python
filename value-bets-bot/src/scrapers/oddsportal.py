"""
oddsportal.py
Scraping logic for OddsPortal (Bet365 odds): league page and match page.
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import date
from typing import Optional


from bs4 import BeautifulSoup
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout, Error as PlaywrightError

from src.core.models import MatchOdds, Odds1x2, OddsDC, OddsBTS, OddsDNB, OddsOU, HtFtSet
from src.utils.browser import accept_cookies
from src.utils.matching import _normalize
from src.config.team_aliases import ALIASES
from src.utils.parsers import parse_float

log = logging.getLogger(__name__)

_OU_LINES = ["1.5", "2.5", "3.5", "4.5"]
_OP_SKIP  = {"outrights", "results", "standings", "archive", "draw"}

# HT/FT outcome → HtFtSet slot
_HTFT_MAP = {
    ("home", "home"): "hh", ("home", "draw"): "hd", ("home", "away"): "ha",
    ("draw", "home"): "dh", ("draw", "draw"): "dd", ("draw", "away"): "da",
    ("away", "home"): "ah", ("away", "draw"): "ad", ("away", "away"): "aa",
}

# Selector que confirma que las odds de Bet365 ya están presentes en el DOM
_BET365_READY = '[data-testid="bookmaker-header"]'

_RETRY_WAIT   = 3.0   # segundos entre reintentos
_MAX_RETRIES  = 2     # número de reintentos (total de intentos = _MAX_RETRIES + 1)


# ── Helpers de espera ─────────────────────────────────────────────────────────

async def _wait_for_bet365(page: Page, timeout: int = 12_000, expected_url: str | None = None) -> bool:
    """
    Espera hasta que las cuotas de Bet365 estén disponibles en el DOM.

    Si se pasa expected_url, primero verifica que la URL actual coincida
    con el partido esperado (detección rápida, sin consumir timeout).
    Luego espera el bookmaker-header con el timeout completo.
    """
    try:
        if expected_url:
            # Verificación rápida de URL sin consumir el timeout principal.
            # OddsPortal es una SPA — la URL suele estar ya correcta tras
            # domcontentloaded, pero si no lo está esperamos brevemente.
            current = page.url
            if expected_url.rstrip("/") not in current:
                try:
                    await page.wait_for_url(
                        f"**{expected_url.rstrip('/')}**", timeout=3_000
                    )
                except Exception:
                    pass  # Continuamos igualmente — el selector dirá la verdad
        await page.wait_for_selector(_BET365_READY, timeout=timeout)
        return True
    except Exception:
        log.debug("[OddsPortal] Cuotas Bet365 no disponibles tras %dms de espera", timeout)
        return False


async def _wait_for_tab_content(page: Page, label: str, timeout: int = 8_000) -> bool:
    """
    Tras hacer click en un tab de mercado, espera a que el tab esté activo
    y las cuotas del nuevo mercado estén disponibles en el DOM.
    """
    try:
        await page.locator(
            f'[data-testid="navigation-active-tab"]:has-text("{label}")'
        ).wait_for(timeout=4_000)
    except Exception:
        pass
    return await _wait_for_bet365(page, timeout=timeout)


# ── League page ───────────────────────────────────────────────────────────────

async def get_today_matches(page: Page, competition: str, url: str) -> list[dict]:
    """Return today's matches from an OddsPortal league page. Retries up to 2 times."""
    log.info(f"[OddsPortal] {competition}: {url}")

    for attempt in range(_MAX_RETRIES + 1):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=40_000)
        except (PlaywrightTimeout, PlaywrightError) as e:
            if attempt < _MAX_RETRIES:
                log.warning(f"[OddsPortal] [{competition}] Error cargando página de liga — reintento {attempt + 1}/{_MAX_RETRIES}")
                await asyncio.sleep(_RETRY_WAIT)
                continue
            log.warning(f"[OddsPortal] [{competition}] Error cargando página de liga tras {_MAX_RETRIES + 1} intentos — descartando")
            return []

        await accept_cookies(page)

        try:
            await page.wait_for_selector('[data-testid="game-row"]', timeout=10_000)
        except Exception:
            log.debug("[OddsPortal] Lista de partidos no visible aún — intentando parsear igualmente")

        matches = _parse_today_matches(await page.content(), url, competition)
        if matches:
            return matches

        if attempt < _MAX_RETRIES:
            log.warning(f"[OddsPortal] [{competition}] No se encontraron partidos — reintento {attempt + 1}/{_MAX_RETRIES}")
            await asyncio.sleep(_RETRY_WAIT)

    return []


def _parse_today_matches(html: str, base_url: str, competition: str) -> list[dict]:
    today  = date.today().isoformat()
    soup   = BeautifulSoup(html, "lxml")
    # Match any OddsPortal match URL regardless of the league path prefix.
    # Some leagues (e.g. Romanian Liga 1) list fixtures under liga-1/ but
    # individual match links resolve under a different slug (e.g. superliga/).
    pat    = re.compile(r'/football/[a-z0-9\-]+/[a-z0-9\-]+/[a-z0-9][a-z0-9\-]+-[A-Za-z0-9]{8}/?')
    seen, matches = set(), []

    today_header = next(
        (el for el in soup.find_all("div", attrs={"data-testid": "date-header"})
         if "today" in el.get_text(strip=True).lower()),
        None,
    )
    if not today_header:
        log.warning("[OddsPortal] Sección 'Hoy' no encontrada en la página de liga")
        return []

    container = today_header.parent.parent.parent
    if not container:
        log.warning("[OddsPortal] Contenedor principal de partidos no encontrado")
        return []

    in_today = False
    for child in container.children:
        if not hasattr(child, "get"):
            continue

        header = child.find("div", attrs={"data-testid": "date-header"})
        if header:
            in_today = "today" in header.get_text(strip=True).lower()

        if not in_today:
            continue

        for row in child.find_all("div", attrs={"data-testid": "game-row"}):
            link = row.find("a", href=pat)
            if not link or link["href"] in seen:
                continue
            href = link["href"]
            if any(s in href for s in _OP_SKIP):
                continue
            seen.add(href)

            home, away = _teams_from_row(row)
            kickoff    = _kickoff_from_row(row, today)
            matches.append({
                "competition": competition,
                "home":    home,
                "away":    away,
                "kickoff": kickoff,
                "url":     f"https://www.oddsportal.com{href}".rstrip("/"),
            })

    log.info(f"[OddsPortal] {len(matches)} matches today in {competition}")
    return matches


def _teams_from_row(row) -> tuple[str, str]:
    participants = row.find(attrs={"data-testid": "event-participants"})
    if participants:
        parts = participants.find_all("p")
        if len(parts) >= 2:
            return parts[0].get_text(strip=True), parts[1].get_text(strip=True)
    parts = row.find_all("p", class_=re.compile(r"participant"))
    if len(parts) >= 2:
        return parts[0].get_text(strip=True), parts[1].get_text(strip=True)
    return "Unknown", "Unknown"


def _kickoff_from_row(row, today: str) -> str:
    time_el = row.find(attrs={"data-testid": "time-item"})
    if time_el:
        m = re.search(r'\b(\d{2}:\d{2})\b', time_el.get_text(strip=True))
        if m:
            return f"{today}T{m.group(1)}"
    m = re.search(r'\b(\d{2}:\d{2})\b', row.get_text())
    return f"{today}T{m.group(1)}" if m else today


# ── Match page ────────────────────────────────────────────────────────────────

async def scrape_match(page: Page, match: dict, markets: frozenset[str] | None = None) -> Optional[MatchOdds]:
    """Scrape Bet365 odds for all markets from an OddsPortal match page. Retries up to 2 times."""
    log.info(f"[OddsPortal] Scraping {match['home']} vs {match['away']}")
    base_url = match["url"].rstrip("/") + "/"
    result   = MatchOdds(
        competition=match.get("competition", ""),
        home_team=match["home"],
        away_team=match["away"],
        kickoff=match["kickoff"],
        source="oddsportal_bet365",
    )

    # ── 1. Cargar la página del partido (con reintentos) ──────────────────────
    loaded = False
    for attempt in range(_MAX_RETRIES + 1):
        try:
            await page.goto(base_url, wait_until="domcontentloaded", timeout=35_000)
            loaded = True
            break
        except (PlaywrightTimeout, PlaywrightError) as e:
            if attempt < _MAX_RETRIES:
                log.warning(
                    f"[OddsPortal] [{match['home']} vs {match['away']}] "
                    f"Error cargando página del partido — reintento {attempt + 1}/{_MAX_RETRIES}"
                )
                await asyncio.sleep(_RETRY_WAIT)
            else:
                log.warning(
                    f"[OddsPortal] [{match['home']} vs {match['away']}] "
                    f"Error cargando página del partido tras {_MAX_RETRIES + 1} intentos — descartando"
                )

    if not loaded:
        return result

    # ── 2. Esperar a Bet365 (con reintentos) ──────────────────────────────────
    # Pasamos la URL esperada para detectar que el DOM pertenece al partido
    # actual y no al partido anterior (evita leer cuotas stale).
    ready = await _wait_for_bet365(page, timeout=12_000, expected_url=base_url)
    if not ready:
        for attempt in range(_MAX_RETRIES):
            log.warning(
                f"[OddsPortal] [{match['home']} vs {match['away']}] "
                f"Cuotas Bet365 no cargaron — recargando página ({attempt + 1}/{_MAX_RETRIES})"
            )
            await asyncio.sleep(_RETRY_WAIT)
            try:
                await page.reload(wait_until="domcontentloaded", timeout=35_000)
            except Exception as e:
                log.warning(f"[OddsPortal] [{match['home']} vs {match['away']}] Error al recargar página: {e}")
                continue
            ready = await _wait_for_bet365(page, timeout=12_000, expected_url=base_url)
            if ready:
                log.info(f"[OddsPortal] [{match['home']} vs {match['away']}] Cuotas Bet365 recuperadas en reintento {attempt + 1}")
                break

        if not ready:
            log.warning(f"[OddsPortal] [{match['home']} vs {match['away']}] Cuotas Bet365 no disponibles tras {_MAX_RETRIES + 1} intentos — continuando sin ellas")

    # ── 3. Extraer cuotas ─────────────────────────────────────────────────────
    ref_1x2: Optional[list[float]] = None
    if markets is None or "1x2" in markets:
        odds = _bet365_odds(await page.content(), 3)
        if odds:
            result.m_1x2 = Odds1x2(home=odds[0], draw=odds[1], away=odds[2])
            ref_1x2 = odds

    ref_dc: Optional[list[float]] = None
    if markets is None or "dc" in markets:
        odds = await _tab_odds(
            page, ["Double Chance", "Doble Oportunidad", "Doble"], 3,
            stale_ref=ref_1x2,
        )
        if odds:
            result.m_dc = OddsDC(home_draw=odds[0], home_away=odds[1], draw_away=odds[2])
            ref_dc = odds

    if markets is None or "bts" in markets:
        odds = await _tab_odds(
            page, ["Both Teams to Score", "BTS", "Ambos equipos"], 2,
            stale_ref=ref_1x2,
            prev_ref=ref_dc[:2] if ref_dc else None,
        )
        if odds:
            result.m_bts = OddsBTS(yes=odds[0], no=odds[1])

    if markets is None or "ou_goals" in markets:
        ou = await _get_ou(page)
        for line_key, attr in [("1.5", "m_ou_goals_15"), ("2.5", "m_ou_goals_25"), ("3.5", "m_ou_goals_35"), ("4.5", "m_ou_goals_45")]:
            if ou.get(line_key):
                setattr(result, attr, OddsOU(over=ou[line_key][0], under=ou[line_key][1]))

    if markets is None or "ht_ft" in markets:
        ht_ft = await _get_ht_ft(page, match)
        if ht_ft:
            result.m_ht_ft = ht_ft

    if markets is None or "dnb" in markets:
        odds = await _tab_odds_js(page, "Draw No Bet", 2)
        if odds:
            result.m_dnb = OddsDNB(home=odds[0], away=odds[1])

    return result


def _is_stale(odds: list[float], ref: Optional[list[float]]) -> bool:
    if not ref or not odds:
        return False
    shared = min(len(odds), len(ref))
    return all(abs(odds[i] - ref[i]) < 0.001 for i in range(shared))


async def _tab_odds(
    page: Page,
    labels: list[str],
    n: int,
    stale_ref: Optional[list[float]] = None,
    prev_ref: Optional[list[float]] = None,
) -> Optional[list[float]]:
    """
    Click a market tab and extract Bet365 odds.

    stale_ref: odds de 1x2 — si el resultado coincide exactamente, el tab
               no cambió respecto a 1x2 (race condition).
    prev_ref:  odds del mercado anterior — permite detectar que el DOM aún
               no actualizó tras el click (e.g. BTS leyendo contenido de DC).

    Cuando se detecta contenido stale, reintenta la lectura hasta 2 veces
    con 2 segundos de espera entre intentos antes de descartar.
    """
    import asyncio
    _READ_RETRIES = 2
    _READ_WAIT    = 2.0

    for text in labels:
        try:
            inactive = page.locator(f'[data-testid="navigation-inactive-tab"]:has-text("{text}")').first
            active   = page.locator(f'[data-testid="navigation-active-tab"]:has-text("{text}")').first

            if await inactive.is_visible(timeout=1800):
                await inactive.click()
                # Esperar que el tab activo cambie al nuevo antes de leer el DOM.
                try:
                    await page.locator(
                        f'[data-testid="navigation-active-tab"]:has-text("{text}")'
                    ).wait_for(timeout=5_000)
                except Exception:
                    pass
                await _wait_for_bet365(page, timeout=8_000)
            elif await active.is_visible(timeout=800):
                await _wait_for_bet365(page, timeout=5_000)
            else:
                continue

            # Intentar leer las odds, reintentando si el DOM aún no actualizó
            for read_attempt in range(_READ_RETRIES + 1):
                odds = _bet365_odds(await page.content(), n)
                if not odds:
                    break

                stale_vs_1x2 = _is_stale(odds, stale_ref)
                stale_vs_prev = prev_ref and _is_stale(odds[:len(prev_ref)], prev_ref)

                if not stale_vs_1x2 and not stale_vs_prev:
                    if read_attempt > 0:
                        log.debug(f"[OddsPortal] Mercado {text}: cuotas correctas obtenidas en reintento {read_attempt}")
                    return odds  # odds válidas

                if read_attempt < _READ_RETRIES:
                    reason = "1x2" if stale_vs_1x2 else "mercado anterior"
                    log.debug(
                        f"[OddsPortal] Mercado {text}: cuotas no actualizadas aún ({reason}) "
                        f"— reintentando lectura {read_attempt + 1}/{_READ_RETRIES}"
                    )
                    await asyncio.sleep(_READ_WAIT)
                else:
                    reason = "1x2" if stale_vs_1x2 else "mercado anterior"
                    log.warning(
                        f"[OddsPortal] Mercado {text}: cuotas idénticas a {reason} "
                        f"tras {_READ_RETRIES + 1} intentos — sin datos fiables, descartando"
                    )

        except Exception:
            pass
    return None


async def _get_ou(page: Page) -> dict:
    result_ou = {}

    try:
        tab = page.locator('[data-testid="navigation-inactive-tab"]:has-text("Over/Under")').first
        if await tab.is_visible(timeout=1800):
            await tab.click()
            await page.locator('[data-testid="navigation-active-tab"]:has-text("Over/Under")').wait_for(timeout=3500)
    except Exception:
        return result_ou

    try:
        await page.wait_for_selector(
            '[data-testid="over-under-collapsed-row"]', timeout=8_000
        )
    except Exception:
        log.debug("[OddsPortal] Líneas Over/Under no cargaron a tiempo")
        return result_ou

    for line in _OU_LINES:
        try:
            rows   = page.locator('[data-testid="over-under-collapsed-row"]')
            target = None
            for i in range(await rows.count()):
                row = rows.nth(i)
                box = row.locator('[data-testid="over-under-collapsed-option-box"]').first
                if not await box.count():
                    continue
                txt = await box.inner_text()
                m   = re.search(r'Over/Under\s*\+?(\d+\.\d+)', txt, re.IGNORECASE)
                if m and m.group(1) == line:
                    target = row
                    break

            if not target:
                continue

            await target.click()
            await page.locator('[data-testid="over-under-expanded-row"]').first.wait_for(timeout=6_000)

            odds = _bet365_ou(await page.content(), line)
            if odds and len(odds) >= 2:
                result_ou[line] = odds[:2]
        except Exception as e:
            log.debug(f"[OddsPortal] Error leyendo Over/Under {line}: {e}")

    return result_ou


async def _get_ht_ft(page: Page, match: dict) -> Optional[HtFtSet]:
    activated = await page.evaluate("""() => {
        const tabs = document.querySelectorAll('[data-testid="navigation-inactive-tab"]');
        for (const tab of tabs) {
            if (tab.textContent.includes('Half Time')) {
                tab.scrollIntoView();
                tab.click();
                return true;
            }
        }
        return false;
    }""")
    if not activated:
        log.debug("[OddsPortal] Tab Descanso/Resultado final no encontrado en la página")
        return None

    try:
        await page.wait_for_selector(
            '[data-testid="over-under-collapsed-row"]', timeout=8_000
        )
    except Exception:
        log.debug("[OddsPortal] Descanso/Resultado final: outcomes no cargaron a tiempo")
        return None

    await page.evaluate("""() => {
        const rows = document.querySelectorAll('[data-testid="over-under-collapsed-row"]');
        for (const row of rows) {
            row.click();
        }
    }""")

    try:
        await page.wait_for_selector(
            '[data-testid="over-under-expanded-row"]', timeout=6_000
        )
    except Exception:
        log.debug("[OddsPortal] Descanso/Resultado final: cuotas expandidas no cargaron a tiempo")
        return None

    raw = await page.evaluate("""() => {
        const results = {};
        const collapsed = document.querySelectorAll('[data-testid="over-under-collapsed-row"]');

        for (const row of collapsed) {
            const box = row.querySelector('[data-testid="over-under-collapsed-option-box"]');
            if (!box) continue;

            const label = box.textContent.trim().replace(/\\d+$/, '').trim();

            const expanded = row.nextElementSibling;
            if (!expanded) continue;

            const bookmakerContainer = expanded.children[0];
            if (!bookmakerContainer) continue;

            for (const bRow of bookmakerContainer.children) {
                const img = bRow.querySelector('img');
                if (img && /^bet365$/i.test(img.alt)) {
                    const oc = bRow.querySelector('[data-testid="odd-container"]');
                    if (oc) results[label] = oc.textContent.trim();
                    break;
                }
            }
        }
        return results;
    }""")

    if not raw:
        return None

    home_n = ALIASES.get(_normalize(match["home"]), _normalize(match["home"]))
    away_n = ALIASES.get(_normalize(match["away"]), _normalize(match["away"]))

    def _classify(token: str) -> Optional[str]:
        t = _normalize(token)
        # Resolver alias (e.g. "psg" → "paris saint germain" canonical)
        t = ALIASES.get(t, t)
        if any(k in t for k in ("draw", "empate")):
            return "draw"
        if any(tok in t for tok in home_n.split() if len(tok) >= 3):
            return "home"
        if any(tok in t for tok in away_n.split() if len(tok) >= 3):
            return "away"
        return None

    ht_ft = HtFtSet()

    for label, price_str in raw.items():
        parts = re.split(r'\s*/\s*', label)
        if len(parts) != 2:
            continue
        ht = _classify(parts[0])
        ft = _classify(parts[1])
        if not ht or not ft:
            log.debug(f"[OddsPortal] Descanso/Resultado final: outcome no clasificado '{label}' (ht={ht}, ft={ft})")
            continue
        slot = _HTFT_MAP.get((ht, ft))
        if not slot:
            continue
        val = parse_float(price_str)
        if val:
            setattr(ht_ft, slot, val)

    if all(getattr(ht_ft, s) is None for s in vars(ht_ft)):
        return None

    return ht_ft


# ── HTML parsers ──────────────────────────────────────────────────────────────

def _bet365_odds(html: str, n: int) -> Optional[list[float]]:
    soup = BeautifulSoup(html, "lxml")
    for header in soup.find_all(attrs={"data-testid": "bookmaker-header"}):
        if not (header.find("img", alt=re.compile(r"^bet365$", re.I)) or
                re.search(r'bet365', header.get_text(), re.I)):
            continue
        row = _find_row_by_testid(header)
        if row:
            prices = _prices(row, n)
            if len(prices) >= n:
                return prices[:n]

    for link in soup.find_all("a", href=re.compile(r"bookmaker/bet365", re.I)):
        if any(k in link.get_text(strip=True).lower() for k in ["claim", "bonus", "review"]):
            continue
        row = _find_row(link)
        if row:
            prices = _prices(row, n)
            if len(prices) >= n:
                return prices[:n]

    log.debug("[OddsPortal] Cuotas de Bet365 no encontradas en la página")
    return None


def _find_row_by_testid(header) -> Optional[object]:
    el = header
    for _ in range(8):
        el = el.parent
        if el is None:
            break
        if len(el.find_all(attrs={"data-testid": re.compile(r"^odd-container")})) >= 2:
            return el
    return None


def _find_row(link) -> Optional[object]:
    el = link
    for _ in range(12):
        el = el.parent
        if el is None:
            break
        if len(el.find_all(attrs={"data-testid": re.compile(r"^odd-container")})) >= 2:
            return el
        if (el.find_all("p", class_=re.compile(r"height-content")) or
                el.find_all(attrs={"data-testid": "odd-container-default"})):
            return el
    return None


def _prices(row, n: int) -> list[float]:
    for finder in [
        lambda r: [parse_float(p.get_text(strip=True)) for p in r.find_all("p", class_=re.compile(r"height-content"))],
        lambda r: [parse_float(a.get_text(strip=True)) for a in r.find_all("a", class_=re.compile(r"odds-link"))],
        lambda r: [parse_float(c.get_text(strip=True)) for c in r.find_all(attrs={"data-testid": re.compile(r"odd-container")})],
    ]:
        prices = [p for p in finder(row) if p]
        if prices:
            return prices[:n]
    return []


def _bet365_ou(html: str, line: str) -> Optional[list[float]]:
    soup = BeautifulSoup(html, "lxml")
    for row in soup.find_all("div", attrs={"data-testid": "over-under-expanded-row"}):
        tc = row.find("div", attrs={"data-testid": "total-container"})
        if not tc or tc.get_text(strip=True).replace("+", "").strip() != line:
            continue
        if not row.find("img", alt=re.compile(r"^bet365$", re.I)):
            continue
        odds = []
        for oc in row.find_all("div", attrs={"data-testid": "odd-container"})[:2]:
            a   = oc.find("a", class_=re.compile(r"odds-link"))
            p   = oc.find("p", class_=re.compile(r"odds-text"))
            val = parse_float((a or p).get_text(strip=True)) if (a or p) else None
            if val:
                odds.append(val)
        if len(odds) == 2:
            return odds
    return None


async def _tab_odds_js(page: Page, label: str, n: int) -> Optional[list[float]]:
    activated = await page.evaluate(f"""() => {{
        const tabs = document.querySelectorAll('[data-testid="navigation-inactive-tab"]');
        for (const tab of tabs) {{
            if (tab.textContent.trim() === '{label}') {{
                tab.scrollIntoView();
                tab.click();
                return true;
            }}
        }}
        return false;
    }}""")
    if not activated:
        log.debug(f"[OddsPortal] Tab '{label}' no encontrado en la página")
        return None

    await _wait_for_tab_content(page, label, timeout=8_000)
    odds = _bet365_odds(await page.content(), n)
    return odds if odds else None
