"""
matching.py
Team name normalisation, fuzzy matching, and match pairing.

All alias/suffix data lives in src/config/team_aliases.py so it can be
updated without touching any logic here.
"""
from __future__ import annotations

import logging
import re
import unicodedata

from src.config.team_aliases import ALIASES, SUFFIXES_PATTERN

log = logging.getLogger(__name__)


# ── Normalisation ─────────────────────────────────────────────────────────────

def _normalize(name: str) -> str:
    """
    Normalise a team name for comparison:
    - Strip diacritics, replace punctuation with spaces,
      remove common suffixes, lowercase, collapse whitespace.
    """
    name = "".join(
        c for c in unicodedata.normalize("NFD", name.strip())
        if unicodedata.category(c) != "Mn"
    )
    name = re.sub(r"[^\w\s]", " ", name)
    name = SUFFIXES_PATTERN.sub("", name.lower())
    return re.sub(r"\s+", " ", name).strip()


# ── Edit distance ─────────────────────────────────────────────────────────────

def _edit_distance(a: str, b: str) -> int:
    """Standard Levenshtein edit distance."""
    if a == b:  return 0
    if not a:   return len(b)
    if not b:   return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            curr.append(min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = curr
    return prev[-1]


# ── Token-level fuzzy match ───────────────────────────────────────────────────

def _tokens_match(ta: set, tb: set) -> bool:
    """
    Every meaningful token (≥ 3 chars) in the shorter set must find a
    partner in the longer set within 1 edit per 5 characters.
    """
    short, long_ = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    meaningful = [t for t in short if len(t) >= 3]
    if not meaningful:
        return False
    return all(
        min(_edit_distance(t, l) for l in long_) <= max(1, len(t) // 5)
        for t in meaningful
    )


# ── Public API ────────────────────────────────────────────────────────────────

def teams_match(a: str, b: str) -> bool:
    """Return True if two team name strings refer to the same club."""
    na = ALIASES.get(_normalize(a), _normalize(a))
    nb = ALIASES.get(_normalize(b), _normalize(b))
    if na == nb or na in nb or nb in na:
        return True
    return _tokens_match(set(na.split()), set(nb.split()))


def pair_matches(
    pinn_matches: list[dict],
    op_matches: list[dict],
) -> list[tuple[dict, dict]]:
    """
    Greedily pair Pinnacle matches with OddsPortal matches by team name similarity.
    Both home and away must match (score = 2) for a pair to be accepted.
    """
    log.info("[Pair] Pinnacle:   " + str([m["home"] + " vs " + m["away"] for m in pinn_matches]))
    log.info("[Pair] OddsPortal: " + str([m["home"] + " vs " + m["away"] for m in op_matches]))
    used, pairs = set(), []
    for pm in pinn_matches:
        best_score, best_op, best_i = 0, None, None
        for i, om in enumerate(op_matches):
            if i in used:
                continue
            score = int(teams_match(pm["home"], om["home"])) + int(teams_match(pm["away"], om["away"]))
            if score > best_score:
                best_score, best_op, best_i = score, om, i
        if best_score >= 2:
            pairs.append((pm, best_op))
            used.add(best_i)
        else:
            log.warning(f"[Pair] No match for: {pm['home']} vs {pm['away']}")
    return pairs
