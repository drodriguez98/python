"""
dedup.py
Deduplication of value bets across loop iterations.

A value bet is identified by: (competition, home_team, away_team, market, outcome).
Once seen, it is suppressed in subsequent iterations UNLESS:
  - bet365_odds  improved by at least MIN_ODDS_DELTA, OR
  - value (EV)   improved by at least MIN_VALUE_DELTA

Small fluctuations in Pinnacle odds cause tiny EV changes that don't warrant
a new notification — the thresholds filter out this noise.

In loop mode the registry lives inside SessionStore.seen_bets — a shared dict
that is persisted by SessionStore.save() as part of the daily session JSON.
BetRegistry does not manage any file directly; it only reads and writes the
dict reference it receives at construction time.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from src.core.models import ValueBet

log = logging.getLogger(__name__)


def _key(bet: ValueBet) -> str:
    return f"{bet.competition}|{bet.home_team}|{bet.away_team}|{bet.market}|{bet.outcome}"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


# ── Umbrales mínimos de mejora para renotificar ──────────────────────────────
# Evita spam por variaciones mínimas de cuota de Pinnacle que cambian el EV
# en décimas pero no representan una oportunidad materialmente distinta.
MIN_ODDS_DELTA  = 0.05   # cuota Bet365 debe subir al menos 0.05
MIN_VALUE_DELTA = 0.01   # EV debe subir al menos 1 punto porcentual


class BetRegistry:
    """
    Deduplication filter backed by an external dict (SessionStore.seen_bets).

    Usage:
        registry = BetRegistry(store.seen_bets)
        bets_to_notify = registry.filter(bets)
        # SessionStore.save() persists the updated seen_bets automatically.
    """

    def __init__(self, seen_bets: dict[str, Any]) -> None:
        # Direct reference to SessionStore._data["seen_bets"] — no copy.
        self._seen = seen_bets
        log.debug(f"[Dedup] Registry initialised ({len(self._seen)} entries)")

    def filter(self, bets: list[ValueBet]) -> list[ValueBet]:
        """
        Return only bets that should trigger a notification:
          - Never seen before, OR
          - bet365_odds improved by at least MIN_ODDS_DELTA (0.05), OR
          - value (EV) improved by at least MIN_VALUE_DELTA (1%)

        Mutates the shared seen_bets dict in-place.
        Caller (scraper.py) is responsible for persisting via SessionStore.save().
        """
        notify: list[ValueBet] = []
        now = _now()

        for bet in bets:
            k    = _key(bet)
            prev = self._seen.get(k)

            if prev is None:
                notify.append(bet)
                self._seen[k] = {
                    "bet365_odds": bet.bet365_odds,
                    "value":       bet.value,
                    "first_seen":  now,
                    "last_seen":   now,
                }
                log.debug(
                    f"[Dedup] NEW — {bet.market.upper()} {bet.outcome} | "
                    f"{bet.home_team} vs {bet.away_team}"
                )
            elif (
                bet.bet365_odds - prev["bet365_odds"] >= MIN_ODDS_DELTA or
                bet.value - prev["value"] >= MIN_VALUE_DELTA
            ):
                notify.append(bet)
                reason = []
                if bet.bet365_odds - prev["bet365_odds"] >= MIN_ODDS_DELTA:
                    reason.append(f"odds {prev['bet365_odds']} → {bet.bet365_odds}")
                if bet.value - prev["value"] >= MIN_VALUE_DELTA:
                    reason.append(f"EV {prev['value']:.1%} → {bet.value:.1%}")
                self._seen[k]["bet365_odds"] = bet.bet365_odds
                self._seen[k]["value"]       = bet.value
                self._seen[k]["last_seen"]   = now
                log.debug(
                    f"[Dedup] IMPROVED ({', '.join(reason)}) — "
                    f"{bet.market.upper()} {bet.outcome} | "
                    f"{bet.home_team} vs {bet.away_team}"
                )
            else:
                self._seen[k]["last_seen"] = now
                log.debug(
                    f"[Dedup] SKIP — {bet.market.upper()} {bet.outcome} | "
                    f"{bet.home_team} vs {bet.away_team}"
                )

        return notify
