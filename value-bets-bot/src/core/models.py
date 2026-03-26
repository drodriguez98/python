"""
models.py
Data structures shared across the whole project.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Odds1x2:
    home: Optional[float] = None
    draw: Optional[float] = None
    away: Optional[float] = None


@dataclass
class OddsDC:
    home_draw: Optional[float] = None
    home_away: Optional[float] = None
    draw_away: Optional[float] = None


@dataclass
class OddsBTS:
    yes: Optional[float] = None
    no:  Optional[float] = None


@dataclass
class OddsDNB:
    home: Optional[float] = None
    away: Optional[float] = None


@dataclass
class OddsOU:
    """Over/Under — used for both goals and corners lines."""
    over:  Optional[float] = None
    under: Optional[float] = None


@dataclass
class HtFtSet:
    """
    Container for Half-Time / Full-Time odds (9 outcomes).
    Naming: first letter = HT result, second = FT result.
      h=home, d=draw, a=away
    """
    hh: Optional[float] = None
    hd: Optional[float] = None
    ha: Optional[float] = None
    dh: Optional[float] = None
    dd: Optional[float] = None
    da: Optional[float] = None
    ah: Optional[float] = None
    ad: Optional[float] = None
    aa: Optional[float] = None


@dataclass
class MatchOdds:
    """All scraped odds for a single match from a single source."""
    competition:        str
    home_team:          str
    away_team:          str
    kickoff:            str
    source:             str
    scraped_at:         str     = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    m_1x2:              Odds1x2 = field(default_factory=Odds1x2)
    m_dc:               OddsDC  = field(default_factory=OddsDC)
    m_bts:              OddsBTS = field(default_factory=OddsBTS)
    m_dnb:              OddsDNB = field(default_factory=OddsDNB)
    m_ou_goals_15:      OddsOU  = field(default_factory=OddsOU)
    m_ou_goals_25:      OddsOU  = field(default_factory=OddsOU)
    m_ou_goals_35:      OddsOU  = field(default_factory=OddsOU)
    m_ou_goals_45:      OddsOU  = field(default_factory=OddsOU)
    m_ht_ft:            HtFtSet = field(default_factory=HtFtSet)
    m_ou_corners_75:    OddsOU  = field(default_factory=OddsOU)
    m_ou_corners_85:    OddsOU  = field(default_factory=OddsOU)
    m_ou_corners_95:    OddsOU  = field(default_factory=OddsOU)
    m_ou_corners_105:   OddsOU  = field(default_factory=OddsOU)
    m_ou_corners_115:   OddsOU  = field(default_factory=OddsOU)

    def to_dict(self) -> dict:
        """Serialize to a nested dict (used for JSON output)."""
        return asdict(self)

    def to_flat(self) -> dict:
        """Serialize to a flat dict keyed by column name (used for value bet analysis)."""
        return {
            "competition": self.competition, "home_team": self.home_team,
            "away_team":   self.away_team,   "kickoff":   self.kickoff,
            "source":      self.source,
            # 1x2
            "1x2_home": self.m_1x2.home, "1x2_draw": self.m_1x2.draw, "1x2_away": self.m_1x2.away,
            # Double Chance
            "dc_home_draw": self.m_dc.home_draw, "dc_home_away": self.m_dc.home_away, "dc_draw_away": self.m_dc.draw_away,
            # BTS
            "bts_yes": self.m_bts.yes, "bts_no": self.m_bts.no,
            # DNB
            "dnb_home": self.m_dnb.home, "dnb_away": self.m_dnb.away,
            # Goals O/U
            "ou_goals_15_over": self.m_ou_goals_15.over, "ou_goals_15_under": self.m_ou_goals_15.under,
            "ou_goals_25_over": self.m_ou_goals_25.over, "ou_goals_25_under": self.m_ou_goals_25.under,
            "ou_goals_35_over": self.m_ou_goals_35.over, "ou_goals_35_under": self.m_ou_goals_35.under,
            "ou_goals_45_over": self.m_ou_goals_45.over, "ou_goals_45_under": self.m_ou_goals_45.under,
            # HT/FT
            "htft_hh": self.m_ht_ft.hh, "htft_hd": self.m_ht_ft.hd, "htft_ha": self.m_ht_ft.ha,
            "htft_dh": self.m_ht_ft.dh, "htft_dd": self.m_ht_ft.dd, "htft_da": self.m_ht_ft.da,
            "htft_ah": self.m_ht_ft.ah, "htft_ad": self.m_ht_ft.ad, "htft_aa": self.m_ht_ft.aa,
            # Corners O/U
            "ou_corners_75_over":  self.m_ou_corners_75.over,  "ou_corners_75_under":  self.m_ou_corners_75.under,
            "ou_corners_85_over":  self.m_ou_corners_85.over,  "ou_corners_85_under":  self.m_ou_corners_85.under,
            "ou_corners_95_over":  self.m_ou_corners_95.over,  "ou_corners_95_under":  self.m_ou_corners_95.under,
            "ou_corners_105_over": self.m_ou_corners_105.over, "ou_corners_105_under": self.m_ou_corners_105.under,
            "ou_corners_115_over": self.m_ou_corners_115.over, "ou_corners_115_under": self.m_ou_corners_115.under,
        }


@dataclass
class ValueBet:
    competition:         str
    home_team:           str
    away_team:           str
    kickoff:             str
    market:              str
    outcome:             str
    pinnacle_odds:       float
    bet365_odds:         float
    pinnacle_prob:       float
    implied_prob:        float
    value:               float
    kelly_fraction:      float = 0.0
    kelly_fraction_half: float = 0.0
