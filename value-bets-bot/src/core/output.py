"""
output.py
Persistence layer for scraped odds and value bets.

Loop mode  — single daily JSON file: output/session_YYYYMMDD.json
             Loaded at startup if it already exists for today, created fresh otherwise.
             All odds, value bets and the dedup registry are consolidated here.

Single run — point-in-time JSON: output/odds_YYYYMMDD_HHMMSS.json
             No session, no persistence.

Session file structure:
{
  "date":        "2026-03-20",
  "iterations":  4,
  "odds":        [ ...MatchOdds dicts... ],
  "value_bets":  [ ...ValueBet dicts... ],
  "seen_bets": {
    "<competition>|<home>|<away>|<market>|<outcome>": {
      "bet365_odds": 15.0,
      "value":       0.1127,
      "first_seen":  "2026-03-20T17:56:20",
      "last_seen":   "2026-03-20T17:59:56"
    }
  }
}
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from src.core.models import MatchOdds, ValueBet

log = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def _session_path(output_dir: Path) -> Path:
    return output_dir / f"session_{date.today().strftime('%Y%m%d')}.json"


def _value_bet_to_dict(b: ValueBet) -> dict:
    return {
        "competition":         b.competition,
        "home_team":           b.home_team,
        "away_team":           b.away_team,
        "kickoff":             b.kickoff,
        "market":              b.market,
        "outcome":             b.outcome,
        "pinnacle_odds":       b.pinnacle_odds,
        "bet365_odds":         b.bet365_odds,
        "pinnacle_prob":       b.pinnacle_prob,
        "implied_prob":        b.implied_prob,
        "value":               b.value,
        "kelly_fraction":      b.kelly_fraction,
        "kelly_fraction_half": b.kelly_fraction_half,
    }


_NON_CORNERS_FIELDS = {
    "m_1x2", "m_dc", "m_bts", "m_dnb",
    "m_ou_goals_15", "m_ou_goals_25", "m_ou_goals_35", "m_ou_goals_45", "m_ht_ft",
}
_CORNERS_FIELDS = {
    "m_ou_corners_75", "m_ou_corners_85", "m_ou_corners_95",
    "m_ou_corners_105", "m_ou_corners_115",
}


def _serialise(r: MatchOdds) -> dict:
    """
    Serialise a MatchOdds to dict, dropping fields that are always null
    for a given source to keep the JSON compact and readable:
      - oddschecker entries:       non-corners markets are omitted
      - oddsportal_bet365 entries: corners fields are omitted
      - all sources:               m_ht_ft omitted when all outcomes are null
    """
    d = asdict(r)
    if r.source == "oddschecker":
        for f in _NON_CORNERS_FIELDS:
            d.pop(f, None)
    elif r.source == "oddsportal_bet365":
        for f in _CORNERS_FIELDS:
            d.pop(f, None)
    # Drop m_ht_ft when not scraped (all outcomes null)
    htft = d.get("m_ht_ft", {})
    if htft and all(v is None for v in htft.values()):
        d.pop("m_ht_ft", None)
    return d



# ── SessionStore ──────────────────────────────────────────────────────────────

class SessionStore:
    """
    Single daily JSON file consolidating odds, value bets and the dedup registry.

    Usage (loop mode):
        store = SessionStore(output_dir)          # load or create for today
        store.add_odds(results)                   # after each competition scrape
        store.add_value_bets(bets_to_notify)      # after dedup filter
        store.increment_iteration()               # once per loop iteration
        store.save()                              # persists everything

    The dedup registry (seen_bets) is accessed directly by BetRegistry via
    store.seen_bets — a plain dict that BetRegistry reads and writes in-place.
    SessionStore.save() persists whatever BetRegistry wrote into it.
    """

    def __init__(self, output_dir: str | Path = "output") -> None:
        self._dir  = Path(output_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = _session_path(self._dir)
        self._data = self._load()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self) -> dict[str, Any]:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                iters = data.get("iterations", 0)
                n_vb  = len(data.get("value_bets", []))
                n_sb  = len(data.get("seen_bets", {}))
                log.debug(
                    f"[Session] Loaded {self._path.name} — "
                    f"{iters} iterations, {n_vb} value bets, {n_sb} seen"
                )
                return data
            except Exception as e:
                log.warning(f"[Session] Could not read {self._path}: {e} — starting fresh")
        log.debug(f"[Session] New session: {self._path.name}")
        return {
            "date":       date.today().isoformat(),
            "iterations": 0,
            "odds":       [],
            "value_bets": [],
            "seen_bets":  {},
        }

    def save(self) -> None:
        try:
            self._path.write_text(
                json.dumps(self._data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            log.debug(f"[Session] Saved → {self._path.name}")
        except Exception as e:
            log.warning(f"[Session] Could not save: {e}")

    # ── Mutators ──────────────────────────────────────────────────────────────

    def increment_iteration(self) -> None:
        self._data["iterations"] += 1

    def add_odds(self, results: list[MatchOdds]) -> None:
        """Upsert scraped odds — keep only the latest reading per (competition, home, away, source)."""
        # Build index of existing records keyed by (competition, home, away, source)
        index: dict[tuple, int] = {
            (r["competition"], r["home_team"], r["away_team"], r["source"]): i
            for i, r in enumerate(self._data["odds"])
        }
        for r in results:
            d   = _serialise(r)
            key = (d["competition"], d["home_team"], d["away_team"], d["source"])
            if key in index:
                self._data["odds"][index[key]] = d   # overwrite with latest
            else:
                index[key] = len(self._data["odds"])
                self._data["odds"].append(d)

    def add_value_bets(self, bets: list[ValueBet]) -> None:
        """Upsert notified value bets — keep only the latest per (competition, home, away, market, outcome)."""
        index: dict[tuple, int] = {
            (r["competition"], r["home_team"], r["away_team"], r["market"], r["outcome"]): i
            for i, r in enumerate(self._data["value_bets"])
        }
        for b in bets:
            d   = _value_bet_to_dict(b)
            key = (d["competition"], d["home_team"], d["away_team"], d["market"], d["outcome"])
            if key in index:
                self._data["value_bets"][index[key]] = d   # overwrite with latest
            else:
                index[key] = len(self._data["value_bets"])
                self._data["value_bets"].append(d)

    # ── Accessors ─────────────────────────────────────────────────────────────

    @property
    def seen_bets(self) -> dict[str, Any]:
        """Direct reference to the seen_bets dict — BetRegistry reads/writes this."""
        return self._data["seen_bets"]

    @property
    def iterations(self) -> int:
        return self._data["iterations"]

    @property
    def path(self) -> Path:
        return self._path


# ── Single-run helper (no session) ───────────────────────────────────────────

def save_json(results: list[MatchOdds], path: Path) -> None:
    """Point-in-time JSON for single-run mode."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump([_serialise(r) for r in results], f, ensure_ascii=False, indent=2)
    log.info(f"Saved JSON: {path}")
