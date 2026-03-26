"""
scraper.py
Orchestrator and CLI entry point.

Usage:
    python scraper.py                                        # All competitions → JSON
    python scraper.py --competition "La Liga"                # Single competition
    python scraper.py --competition "La Liga" "Serie A"      # Multiple competitions
    python scraper.py --category league_europe               # All European leagues
    python scraper.py --category domestic_cup continental    # Multiple categories
    python scraper.py --threshold 0.02                       # Custom edge threshold
    python scraper.py --markets 1x2 ou                       # Only selected markets
    python scraper.py --min-odd 1.5 --max-odd 5.0            # Pinnacle odds range filter
    python scraper.py --no-headless                          # Show browser (debug)
    python scraper.py --debug                                # Verbose logging
    python scraper.py --loop                                 # Run continuously (Ctrl+C to stop)
    python scraper.py --list-competitions                    # List all competition names
    python scraper.py --list-categories                      # List available categories
    python scraper.py --list-markets                         # List available markets
"""
from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import argparse
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Page

from src.scrapers import pinnacle, oddsportal
from src.scrapers import oddschecker
from src.core.analysis import find_value_bets, print_value_bets
from src.core.telegram import telegram_send_bets
from src.core.models import MatchOdds
from src.core.output import SessionStore, save_json
from src.core.dedup import BetRegistry
from src.config.competitions import CATEGORIES, COMPETITIONS, resolve_targets
from src.utils.browser import configure_page, make_browser_context
from src.utils.matching import pair_matches

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Markets ───────────────────────────────────────────────────────────────────

ALL_MARKETS: dict[str, str] = {
    "1x2":          "Victoria local / Empate / Victoria visitante",
    "dc":           "Doble oportunidad (1X, 12, X2)",
    "bts":          "Ambos equipos marcan (Sí / No)",
    "dnb":          "Victoria sin empate (Draw No Bet)",
    "ou_goals":     "Over/Under goles: 1.5, 2.5, 3.5 y 4.5",
    "ht_ft":        "Descanso / Resultado final",
    "ou_corners":   "Over/Under corners: 7.5, 8.5, 9.5, 10.5 y 11.5",
}

DEFAULT_MARKETS: frozenset[str] = frozenset(m for m in ALL_MARKETS if m != "ht_ft")


# ── Competition orchestrator ──────────────────────────────────────────────────

def _build_oc_match_url(oc_base_url: str, home: str, away: str) -> str:
    """
    Build an Oddschecker match URL from the league base URL and team names.
    E.g.: base='https://www.oddschecker.com/es/futbol/espana/primera-division'
          home='Real Madrid', away='Atletico Madrid'
          -> '.../real-madrid-v-atletico-madrid'
    """
    import re
    import unicodedata

    def slugify(name: str) -> str:
        name = unicodedata.normalize('NFKD', name)
        name = name.encode('ascii', 'ignore').decode('ascii')
        name = name.lower()
        name = re.sub(r'[^a-z0-9]+', '-', name)
        return name.strip('-')

    base = oc_base_url.rstrip('/')
    return f'{base}/{slugify(home)}-v-{slugify(away)}'


async def _scrape_competition(
    page_pinn: Page, page_op: Page, page_oc: Page,
    name: str, pinn_url: str, op_url: str, oc_url: Optional[str],
    markets: frozenset[str] = DEFAULT_MARKETS,
) -> list[MatchOdds]:
    """
    Scrape one competition end-to-end:
    1. Fetch today's matches from Pinnacle and OddsPortal.
    2. Pair by team name.
    3. Scrape match-level odds for each paired match.
    4. Scrape corners via Oddschecker using pre-built URLs.
    5. Scrape Pinnacle-only for unpaired matches.
    """
    log.info(f"\n{'='*55}\n{name}\n{'='*55}")
    results: list[MatchOdds] = []

    pinn_matches = await pinnacle.get_today_matches(page_pinn, name, pinn_url)
    op_matches   = await oddsportal.get_today_matches(page_op, name, op_url)

    if not pinn_matches and not op_matches:
        log.info(f"No matches today for {name}")
        return results

    pairs            = pair_matches(pinn_matches, op_matches) if (pinn_matches and op_matches) else []
    paired_pinn_urls = {p["url"] for p, _ in pairs}

    for pm, om in pairs:
        # OddsPortal usa el nombre canónico de Pinnacle para que find_value_bets
        # pueda agrupar ambas filas por la misma clave (competition, home, away)
        om_canonical = {**om, "home": pm["home"], "away": pm["away"]}
        for fn, match, label, pg in [
            (pinnacle.scrape_match,   pm,           "Pinnacle",   page_pinn),
            (oddsportal.scrape_match, om_canonical, "OddsPortal", page_op),
        ]:
            try:
                odds = await fn(pg, match, markets)
                if odds:
                    results.append(odds)
            except Exception as e:
                log.error(f"[{label}] Error scraping {match['home']}: {e}")

    for pm in pinn_matches:
        if pm["url"] not in paired_pinn_urls:
            try:
                odds = await pinnacle.scrape_match(page_pinn, pm, markets)
                if odds:
                    results.append(odds)
            except Exception as e:
                log.error(f"[Pinnacle] Unmatched {pm['home']}: {e}")

    # ── Corners via Oddschecker ───────────────────────────────────────────────
    if "ou_corners" in markets and oc_url and pinn_matches:
        for pm in pinn_matches:
            oc_match_url = _build_oc_match_url(oc_url, pm["home"], pm["away"])
            oc_match = {
                "competition": pm["competition"],
                "home":        pm["home"],
                "away":        pm["away"],
                "kickoff":     pm["kickoff"],
                "url":         oc_match_url,
            }
            try:
                oc_odds = await oddschecker.scrape_match(page_oc, oc_match)
                if oc_odds:
                    results.append(oc_odds)
            except Exception as e:
                log.error(f"[Oddschecker] Error scraping {pm['home']}: {e}")

    return results


# ── Single run ────────────────────────────────────────────────────────────────

async def _run_once(
    competitions: Optional[list[str]] = None,
    categories: Optional[list[str]] = None,
    headless: bool = True,
    output_dir: str = "output",
    threshold: Optional[float] = None,
    markets: frozenset[str] = DEFAULT_MARKETS,
    min_odd: Optional[float] = None,
    max_odd: Optional[float] = None,
    store: Optional[SessionStore] = None,
) -> list[MatchOdds]:
    """Execute one full scraping pass over all target competitions."""
    targets = resolve_targets(competitions, categories)
    all_results: list[MatchOdds] = []
    out_dir = Path(output_dir)
    out_dir.mkdir(exist_ok=True)

    # In loop mode a shared BetRegistry is built from the session's seen_bets dict
    registry = BetRegistry(store.seen_bets) if store is not None else None

    async with async_playwright() as pw:
        browser, ctx = await make_browser_context(pw, headless)
        page_pinn, page_op = await ctx.new_page(), await ctx.new_page()
        for p in (page_pinn, page_op):
            await configure_page(p)

        # Oddschecker gets its own isolated browser context to avoid Cloudflare
        _, ctx_oc = await make_browser_context(pw, headless)
        page_oc = await ctx_oc.new_page()
        await configure_page(page_oc)

        for name in targets:
            if name not in COMPETITIONS:
                log.warning(f"Unknown competition: {name}")
                continue

            results: list[MatchOdds] = []
            try:
                comp_entry = COMPETITIONS[name]
                pinn_url = comp_entry[0]
                op_url   = comp_entry[1]
                oc_url   = comp_entry[2] if len(comp_entry) > 2 else None
                results = await _scrape_competition(
                    page_pinn, page_op, page_oc,
                    name, pinn_url, op_url, oc_url,
                    markets=markets,
                )
                all_results.extend(results)
            except Exception as e:
                log.error(f"Error in {name}: {e}")

            bets = find_value_bets(
                results, threshold=threshold, markets=markets,
                min_odd=min_odd, max_odd=max_odd,
            )

            if store is not None:
                # Loop mode — deduplicate, then persist everything into the session
                store.add_odds(results)
                bets_to_notify = registry.filter(bets)
                if bets_to_notify:
                    store.add_value_bets(bets_to_notify)
                store.save()

                print_value_bets(bets_to_notify)
                if bets_to_notify:
                    telegram_send_bets(bets_to_notify)
                elif bets:
                    log.info(f"  {len(bets)} value bet(s) found but already notified (no improvement).")
            else:
                # Single-run mode — no dedup, no session
                print_value_bets(bets)
                if bets:
                    telegram_send_bets(bets)

        try:
            await asyncio.wait_for(browser.close(), timeout=15.0)
        except Exception:
            pass
        try:
            await asyncio.wait_for(ctx_oc.close(), timeout=10.0)
        except Exception:
            pass

    # Single-run: save a point-in-time JSON and exit
    if store is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path  = out_dir / f"odds_{timestamp}.json"
        save_json(all_results, out_path)
        log.info(f"\n✅ Done. {len(all_results)} records → {out_path}")
    else:
        log.info(f"\n✅ Done. {len(all_results)} records → {store.path.name}")

    return all_results


# ── Continuous loop ───────────────────────────────────────────────────────────

async def run_loop(
    competitions: Optional[list[str]] = None,
    categories: Optional[list[str]] = None,
    headless: bool = True,
    output_dir: str = "output",
    threshold: Optional[float] = None,
    markets: frozenset[str] = DEFAULT_MARKETS,
    min_odd: Optional[float] = None,
    max_odd: Optional[float] = None,
) -> None:
    """
    Run scraping passes back-to-back indefinitely.
    Each pass starts immediately after the previous one finishes.
    Stop cleanly with Ctrl+C.
    """
    Path(output_dir).mkdir(exist_ok=True)
    store = SessionStore(output_dir)
    log.debug(
        f"[Session] {store.path.name} — "
        f"{store.iterations} previous iterations, "
        f"{len(store.seen_bets)} seen bets"
    )

    iteration = 0
    while True:
        iteration += 1
        store.increment_iteration()
        log.info(
            f"\n{'#'*55}\n"
            f"  ITERATION {store.iterations} — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{'#'*55}"
        )
        await _run_once(
            competitions=competitions,
            categories=categories,
            headless=headless,
            output_dir=output_dir,
            threshold=threshold,
            markets=markets,
            min_odd=min_odd,
            max_odd=max_odd,
            store=store,
        )
        log.info(f"  Iteration {store.iterations} complete. Starting next pass immediately…\n")


# ── Public alias (backwards compatible) ──────────────────────────────────────

async def run(
    competitions: Optional[list[str]] = None,
    categories: Optional[list[str]] = None,
    headless: bool = True,
    output_dir: str = "output",
    threshold: Optional[float] = None,
    markets: frozenset[str] = DEFAULT_MARKETS,
    min_odd: Optional[float] = None,
    max_odd: Optional[float] = None,
) -> list[MatchOdds]:
    """Alias for _run_once() kept for backwards compatibility."""
    return await _run_once(
        competitions=competitions,
        categories=categories,
        headless=headless,
        output_dir=output_dir,
        threshold=threshold,
        markets=markets,
        min_odd=min_odd,
        max_odd=max_odd,
    )


# ── CLI ───────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Daily football odds scraper (Pinnacle + OddsPortal/Bet365)"
    )

    target = p.add_mutually_exclusive_group()
    target.add_argument("--competition", "-c", nargs="+", metavar="NAME",
                        help="One or more competition names")
    target.add_argument("--category", "-C", nargs="+", metavar="CATEGORY",
                        help="One or more category slugs (see --list-categories)")

    p.add_argument("--output-dir", "-d", default="output",
                   help="Output directory (default: ./output)")
    p.add_argument("--no-headless", action="store_true",
                   help="Show browser window")
    p.add_argument("--debug", action="store_true",
                   help="Enable DEBUG logging")
    p.add_argument("--list-competitions", action="store_true",
                   help="Print all available competition names and exit")
    p.add_argument("--list-categories", action="store_true",
                   help="Print all available categories and exit")
    p.add_argument("--list-markets", action="store_true",
                   help="Print all available markets and exit")
    p.add_argument("--threshold", "-t", type=float, default=None,
                   help=(
                       "Minimum value edge, applied to all markets. "
                       "If omitted, per-market thresholds are used "
                       "(1x2=3%%, dc=4%%, bts=5%%, dnb=4%%, ou_goals=4%%, ou_corners=5%%, ht_ft=excluded). "
                       "Useful for exploration: --threshold 0.00"
                   ))
    p.add_argument("--markets", "-m", nargs="+", metavar="MARKET",
                   choices=list(ALL_MARKETS),
                   help="Markets to scrape (default: all). Options: 1x2 dc bts dnb ou_goals ou_corners ht_ft")
    p.add_argument("--loop", "-L", action="store_true",
                   help="Run continuously: restart immediately after each pass (Ctrl+C to stop)")
    p.add_argument("--min-odd", type=float, default=None,
                   help="Minimum Pinnacle odds to report a value bet")
    p.add_argument("--max-odd", type=float, default=None,
                   help="Maximum Pinnacle odds to report a value bet")
    return p


def main() -> None:
    args = _build_parser().parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.list_competitions:
        for name in COMPETITIONS:
            print(f"  - {name}")
        return

    if args.list_categories:
        for slug, meta in CATEGORIES.items():
            print(f"\n  {slug}  —  {meta['label']}")
            for name in meta["competitions"]:
                print(f"      · {name}")
        print()
        return

    if args.list_markets:
        for key, desc in ALL_MARKETS.items():
            print(f"  {key:<6}  {desc}")
        return

    kwargs = dict(
        competitions=args.competition,
        categories=args.category,
        headless=not args.no_headless,
        output_dir=args.output_dir,
        threshold=args.threshold,
        # Si el usuario pasa --markets, se usa exactamente esa selección.
        # Excepción: si incluye ht_ft junto a otros mercados, se respeta.
        # Si pasa solo ht_ft sin otros, se añade a DEFAULT_MARKETS.
        markets=(
            DEFAULT_MARKETS | frozenset(args.markets)
            if args.markets and frozenset(args.markets) <= {"ht_ft"}
            else frozenset(args.markets) if args.markets
            else DEFAULT_MARKETS
        ),
        min_odd=args.min_odd,
        max_odd=args.max_odd,
    )

    if args.loop:
        log.info("🔁 Loop mode enabled — press Ctrl+C to stop.")
        try:
            asyncio.run(run_loop(**kwargs))
        except KeyboardInterrupt:
            log.info("\n⛔ Stopped by user (Ctrl+C). Goodbye.")
        except Exception as e:
            log.critical(f"\n💥 Unexpected error — bot stopped: {e}", exc_info=True)
            raise SystemExit(1)
    else:
        try:
            asyncio.run(_run_once(**kwargs))
        except KeyboardInterrupt:
            log.info("\n⛔ Stopped by user (Ctrl+C).")
        except Exception as e:
            log.critical(f"\n💥 Unexpected error: {e}", exc_info=True)
            raise SystemExit(1)


if __name__ == "__main__":
    main()
