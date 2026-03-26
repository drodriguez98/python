"""
analysis.py
Value-bet detection: Pinnacle demarginisation vs Bet365.
"""
from __future__ import annotations

import logging
from typing import Optional

from src.core.models import MatchOdds, ValueBet

log = logging.getLogger(__name__)


def _kelly_fraction(prob: float, decimal_odds: float) -> float:
    b = decimal_odds - 1.0
    if b <= 0 or prob <= 0 or prob >= 1:
        return 0.0
    f = (prob * b - (1.0 - prob)) / b
    return round(max(0.0, min(f, 0.25)), 4)


# Markets: key → [(outcome_name, flat_dict_column)]
_MARKETS = [
    ("1x2", [("home", "1x2_home"), ("draw", "1x2_draw"), ("away", "1x2_away")]),
    ("dc",  [("1X",  "dc_home_draw"), ("12",  "dc_home_away"), ("X2",  "dc_draw_away")]),
    ("bts", [("yes", "bts_yes"), ("no",  "bts_no")]),
    ("dnb", [("home","dnb_home"), ("away","dnb_away")]),
    ("ou_goals_15", [("over", "ou_goals_15_over"), ("under", "ou_goals_15_under")]),
    ("ou_goals_25", [("over", "ou_goals_25_over"), ("under", "ou_goals_25_under")]),
    ("ou_goals_35", [("over", "ou_goals_35_over"), ("under", "ou_goals_35_under")]),
    ("ou_goals_45", [("over", "ou_goals_45_over"), ("under", "ou_goals_45_under")]),
    ("ht_ft", [
        ("home/home", "htft_hh"), ("home/draw", "htft_hd"), ("home/away", "htft_ha"),
        ("draw/home", "htft_dh"), ("draw/draw", "htft_dd"), ("draw/away", "htft_da"),
        ("away/home", "htft_ah"), ("away/draw", "htft_ad"), ("away/away", "htft_aa"),
    ]),
    ("ou_corners_75",  [("over", "ou_corners_75_over"),  ("under", "ou_corners_75_under")]),
    ("ou_corners_85",  [("over", "ou_corners_85_over"),  ("under", "ou_corners_85_under")]),
    ("ou_corners_95",  [("over", "ou_corners_95_over"),  ("under", "ou_corners_95_under")]),
    ("ou_corners_105", [("over", "ou_corners_105_over"), ("under", "ou_corners_105_under")]),
    ("ou_corners_115", [("over", "ou_corners_115_over"), ("under", "ou_corners_115_under")]),
]


MARKET_THRESHOLDS: dict[str, float] = {
    "1x2":          0.03,
    "dc":           0.04,
    "bts":          0.05,
    "dnb":          0.04,
    "ou_goals_15":  0.04,
    "ou_goals_25":  0.04,
    "ou_goals_35":  0.04,
    "ou_goals_45":  0.04,
    "ht_ft":        0.08,
    "ou_corners_75":  0.05,
    "ou_corners_85":  0.05,
    "ou_corners_95":  0.05,
    "ou_corners_105": 0.05,
    "ou_corners_115": 0.05,
}


def _demargin(odds: list[float]) -> list[float]:
    if not odds or any(o <= 1.0 for o in odds):
        return []
    raw   = [1.0 / o for o in odds]
    total = sum(raw)
    return [p / total for p in raw]


_HTFT_MAX_MARGIN   = 0.15
_HTFT_MIN_OUTCOMES = 6


def _demargin_htft(
    outcomes: list[tuple[str, str]],
    pin: dict,
    b365: dict,
) -> list[tuple[str, float, float, float, float]] | None:
    valid = []
    for outcome_name, col in outcomes:
        try:
            p = float(pin.get(col) or 0)
            b = float(b365.get(col) or 0)
        except (ValueError, TypeError):
            continue
        if p > 1.0 and b > 1.0:
            valid.append((outcome_name, p, b))

    if len(valid) < _HTFT_MIN_OUTCOMES:
        log.debug(f"[HT/FT] Descartado: solo {len(valid)}/9 outcomes válidos (mínimo {_HTFT_MIN_OUTCOMES})")
        return None

    pin_odds = [p for _, p, _ in valid]
    margin   = sum(1.0 / o for o in pin_odds) - 1.0
    if margin > _HTFT_MAX_MARGIN:
        log.debug(f"[HT/FT] Descartado: margen Pinnacle {margin:.2%} supera {_HTFT_MAX_MARGIN:.2%}")
        return None

    probs = _demargin(pin_odds)
    return [
        (name, p_odd, b_odd, prob, round(1.0 / b_odd, 4))
        for (name, p_odd, b_odd), prob in zip(valid, probs)
    ]


def _market_active(key: str, markets: frozenset[str] | None) -> bool:
    if markets is None:
        return True
    if key.startswith("ou_goals_"):
        return "ou_goals" in markets
    if key.startswith("ou_corners_"):
        return "ou_corners" in markets
    return key in markets


def find_value_bets(
    results: list[MatchOdds],
    threshold: Optional[float] = None,
    markets: frozenset[str] | None = None,
    min_odd: Optional[float] = None,
    max_odd: Optional[float] = None,
) -> list[ValueBet]:
    active_markets = [(k, v) for k, v in _MARKETS if _market_active(k, markets)]

    grouped: dict[tuple, dict] = {}
    for r in results:
        key = (r.competition, r.home_team, r.away_team)
        grouped.setdefault(key, {})[r.source] = r.to_flat()

    bets: list[ValueBet] = []
    for (comp, home, away), sources in grouped.items():
        pin  = sources.get("pinnacle")
        b365 = sources.get("oddsportal_bet365")
        oc   = sources.get("oddschecker")
        if not pin:
            continue

        kickoff = pin.get("kickoff", "")

        def _b365_vals(cols):
            try:
                return [float(b365.get(c) or 0) for _, c in cols] if b365 else []
            except Exception:
                return []
        b365_1x2 = _b365_vals([o for o in _MARKETS[0][1]])

        for market_key, outcomes in active_markets:
            is_corners = market_key.startswith("ou_corners_")
            retail     = oc if is_corners else b365
            if not retail:
                continue

            # ── HT/FT ────────────────────────────────────────────────────────
            if market_key == "ht_ft":
                htft_valid = _demargin_htft(outcomes, pin, retail)
                if not htft_valid:
                    continue
                for outcome_name, pin_odd, b365_odd, prob, impl_prob in htft_valid:
                    if min_odd is not None and pin_odd < min_odd: continue
                    if max_odd is not None and pin_odd > max_odd: continue
                    mkt_thr = threshold if threshold is not None else MARKET_THRESHOLDS.get("ht_ft")
                    value = prob * b365_odd - 1.0
                    if value >= mkt_thr:
                        kf = _kelly_fraction(prob, b365_odd)
                        bets.append(ValueBet(
                            competition=comp, home_team=home, away_team=away,
                            kickoff=kickoff, market=market_key, outcome=outcome_name,
                            pinnacle_odds=pin_odd, bet365_odds=b365_odd,
                            pinnacle_prob=round(prob, 4), implied_prob=impl_prob,
                            value=round(value, 4), kelly_fraction=kf,
                            kelly_fraction_half=round(kf / 2, 4),
                        ))
                continue

            # ── Resto de mercados ─────────────────────────────────────────────
            pin_odds: list[Optional[float]] = []
            for _, col in outcomes:
                try:
                    v = float(pin.get(col) or 0)
                    pin_odds.append(v if v > 1.0 else None)
                except (ValueError, TypeError):
                    pin_odds.append(None)

            if any(o is None for o in pin_odds):
                continue

            # Sanidad DC/BTS
            if market_key in ("dc", "bts") and b365_1x2 and b365:
                b365_market = _b365_vals(outcomes)
                shared = min(len(b365_market), len(b365_1x2))
                if shared > 0 and all(abs(b365_market[i] - b365_1x2[i]) < 0.001 for i in range(shared)):
                    log.warning(f"[Analysis] {home} vs {away} — {market_key.upper()} idéntico a 1x2, descartando")
                    continue

            probs = _demargin(pin_odds)  # type: ignore[arg-type]
            if not probs:
                continue

            for i, (outcome_name, col) in enumerate(outcomes):
                try:
                    retail_odd = float(retail.get(col) or 0)
                except (ValueError, TypeError):
                    continue
                if retail_odd <= 1.0: continue
                if min_odd is not None and pin_odds[i] < min_odd: continue
                if max_odd is not None and pin_odds[i] > max_odd: continue

                mkt_thr = threshold if threshold is not None else MARKET_THRESHOLDS.get(market_key, 0.03)
                value = probs[i] * retail_odd - 1.0
                if value >= mkt_thr:
                    kf = _kelly_fraction(probs[i], retail_odd)
                    bets.append(ValueBet(
                        competition=comp, home_team=home, away_team=away,
                        kickoff=kickoff, market=market_key, outcome=outcome_name,
                        pinnacle_odds=pin_odds[i],  # type: ignore[arg-type]
                        bet365_odds=retail_odd,
                        pinnacle_prob=round(probs[i], 4),
                        implied_prob=round(1.0 / retail_odd, 4),
                        value=round(value, 4), kelly_fraction=kf,
                        kelly_fraction_half=round(kf / 2, 4),
                    ))

    return sorted(bets, key=lambda b: b.value, reverse=True)


def print_value_bets(bets: list[ValueBet]) -> None:
    if not bets:
        log.info("No value bets found.")
        return
    print(f"\n{'='*60}\n  VALUE BETS: {len(bets)}\n{'='*60}")
    for b in bets:
        kelly_line = (
            f"  Kelly:    {b.kelly_fraction:.1%} bankroll  "
            f"(½Kelly recomendado: {b.kelly_fraction_half:.1%})\n"
            if b.kelly_fraction > 0 else ""
        )
        print(
            f"\n  {b.competition} | {b.kickoff}\n"
            f"  {b.home_team} vs {b.away_team}\n"
            f"  Market: {b.market.upper()} → {b.outcome.upper()}\n"
            f"  Pinnacle: {b.pinnacle_odds:.2f}  (real prob: {b.pinnacle_prob:.1%})\n"
            f"  Bet365:   {b.bet365_odds:.2f}  (impl prob: {b.implied_prob:.1%})\n"
            f"  Value:    +{b.value:.1%}\n"
            f"{kelly_line}"
        )
    print(f"\n{'='*60}\n")
