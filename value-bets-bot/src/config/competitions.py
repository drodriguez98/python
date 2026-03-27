"""
competitions.py
Central registry: competition name → (Pinnacle URL, OddsPortal URL[, Oddschecker URL]).

The optional third element is the Oddschecker league URL used to scrape
Bet365 corners Over/Under odds. Competitions without this URL will not
have corners scraped.

To add a competition:
  1. Pick a readable name (used in CLI and Telegram messages).
  2. Add a tuple: ("pinnacle_url", "oddsportal_url") or
                  ("pinnacle_url", "oddsportal_url", "oddschecker_url").
  3. Assign it to a category in CATEGORIES below.

Available categories:
  - league_europe
  - league_americas
  - league_asia
  - domestic_cup
  - continental
"""
from __future__ import annotations

from typing import Optional

# fmt: off
COMPETITIONS: dict[str, tuple] = {

    # ── National leagues — Europe ────────────────────────────────────────────
    "Austrian Bundesliga":   ("https://www.pinnacle.com/es/soccer/austria-bundesliga/matchups/",                "https://www.oddsportal.com/football/austria/bundesliga/",                              "https://www.oddschecker.com/es/futbol/austria/bundesliga/"),
    "Belgium Pro League":    ("https://www.pinnacle.com/es/soccer/belgium-pro-league/matchups/",                "https://www.oddsportal.com/football/belgium/jupiler-pro-league/",                      "https://www.oddschecker.com/es/futbol/belgica/jupiler-league/"),
    "Bundesliga":            ("https://www.pinnacle.com/es/soccer/germany-bundesliga/matchups/",                "https://www.oddsportal.com/football/germany/bundesliga/",                              "https://www.oddschecker.com/es/futbol/alemania/bundesliga/"),
    "Czech First League":    ("https://www.pinnacle.com/es/soccer/czech-republic-first-liga/matchups/",         "https://www.oddsportal.com/football/czech-republic/chance-liga/"),
    "Danish Superliga":      ("https://www.pinnacle.com/es/soccer/denmark-superliga/matchups/",                 "https://www.oddsportal.com/football/denmark/superliga/",                               "https://www.oddschecker.com/es/futbol/dinamarca/superliga/"),
    "Eredivisie":            ("https://www.pinnacle.com/es/soccer/netherlands-eredivisie/matchups/",            "https://www.oddsportal.com/football/netherlands/eredivisie/",                          "https://www.oddschecker.com/es/futbol/paises-bajos/eredivisie/"),
    "Greek Super League":    ("https://www.pinnacle.com/es/soccer/greece-super-league/matchups/",               "https://www.oddsportal.com/football/greece/super-league/",                             "https://www.oddschecker.com/es/futbol/grecia/superliga/"),
    "La Liga":               ("https://www.pinnacle.com/es/soccer/spain-la-liga/matchups/",                     "https://www.oddsportal.com/football/spain/laliga/",                                    "https://www.oddschecker.com/es/futbol/espana/primera-division/"),
    "Ligue 1":               ("https://www.pinnacle.com/es/soccer/france-ligue-1/matchups/",                    "https://www.oddsportal.com/football/france/ligue-1/",                                  "https://www.oddschecker.com/es/futbol/francia/ligue-1/"),
    "Norway Eliteserien":    ("https://www.pinnacle.com/es/soccer/norway-eliteserien/matchups/",                "https://www.oddsportal.com/football/norway/eliteserien/",                              "https://www.oddschecker.com/es/futbol/noruega/eliteserien/"),             
    "Poland Ekstraklasa":    ("https://www.pinnacle.com/es/soccer/poland-ekstraklasa/matchups/",                "https://www.oddsportal.com/football/poland/ekstraklasa/",                              "https://www.oddschecker.com/es/futbol/polonia/ekstraklasa/"),
    "Premier League":        ("https://www.pinnacle.com/es/soccer/england-premier-league/matchups/",            "https://www.oddsportal.com/football/england/premier-league/",                          "https://www.oddschecker.com/es/futbol/inglaterra/premier-league/"),
    "Primeira Liga":         ("https://www.pinnacle.com/es/soccer/portugal-primeira-liga/matchups/",            "https://www.oddsportal.com/football/portugal/liga-portugal/",                          "https://www.oddschecker.com/es/futbol/portugal/primeira-liga/"),
    "Romanian Liga 1":       ("https://www.pinnacle.com/es/soccer/romania-liga-1/matchups/",                    "https://www.oddsportal.com/football/romania/liga-1/",                                  "https://www.oddschecker.com/es/futbol/rumania/liga-I/"),
    "Russia Premier League": ("https://www.pinnacle.com/es/soccer/russia-premier-league/matchups/",             "https://www.oddsportal.com/football/russia/premier-league/"),
    "Scottish Premiership":  ("https://www.pinnacle.com/es/soccer/scotland-premiership/matchups/",              "https://www.oddsportal.com/football/scotland/premiership/",                            "https://www.oddschecker.com/es/futbol/escocia/premiership/"),
    "Serie A":               ("https://www.pinnacle.com/es/soccer/italy-serie-a/matchups/",                     "https://www.oddsportal.com/football/italy/serie-a/",                                   "https://www.oddschecker.com/es/futbol/italia/serie-a/"),
    "Super Lig":             ("https://www.pinnacle.com/es/soccer/turkey-super-league/matchups/",               "https://www.oddsportal.com/football/turkey/super-lig/",                                "https://www.oddschecker.com/es/futbol/turquia/super-lig/"),
    "Swedish Allsvenskan":   ("https://www.pinnacle.com/es/soccer/sweden-allsvenskan/matchups/",                "https://www.oddsportal.com/football/sweden/allsvenskan/",                              "https://www.oddschecker.com/es/futbol/suecia"),
    "Swiss Super League":    ("https://www.pinnacle.com/es/soccer/switzerland-super-league/matchups/",          "https://www.oddsportal.com/football/switzerland/super-league/",                        "https://www.oddschecker.com/es/futbol/suiza/superliga/"),

    # ── National leagues — Americas ──────────────────────────────────────────
    "Argentina Liga Pro":    ("https://www.pinnacle.com/es/soccer/argentina-liga-pro/matchups/",                "https://www.oddsportal.com/football/argentina/liga-profesional/",                      "https://www.oddschecker.com/football/world/argentina/primera-division"),
    "Brasileirao":           ("https://www.pinnacle.com/es/soccer/brazil-serie-a/matchups/",                    "https://www.oddsportal.com/football/brazil/serie-a-betano/",                           "https://www.oddschecker.com/es/futbol/brasil/serie-a/"),
    "Liga AUF":		     ("https://www.pinnacle.com/es/soccer/uruguay-primera-division/matchups/",		        "https://www.oddsportal.com/football/uruguay/liga-auf-uruguaya/",			            "https://www.oddschecker.com/es/futbol/uruguay/primera-division"),
    "Liga de Primera":       ("https://www.pinnacle.com/es/soccer/chile-primera-division/matchups/",            "https://www.oddsportal.com/football/chile/liga-de-primera/",                           "https://www.oddschecker.com/es/futbol/chile/primera-division"),
    "Liga MX":               ("https://www.pinnacle.com/es/soccer/mexico-liga-mx/matchups/",                    "https://www.oddsportal.com/football/mexico/liga-mx/",                                  "https://www.oddschecker.com/es/futbol/mexico/liga-mx/"),
    "MLS":                   ("https://www.pinnacle.com/es/soccer/usa-major-league-soccer/matchups/",           "https://www.oddsportal.com/football/usa/mls/",                                         "https://www.oddschecker.com/es/futbol/usa/mls/"),
    "Primera A":             ("https://www.pinnacle.com/es/soccer/colombia-primera-a/matchups/",                "https://www.oddsportal.com/football/colombia/primera-a/",                              "https://www.oddschecker.com/es/futbol/colombia/primera-a/"),

    # ── National leagues — Asia / Oceania ────────────────────────────────────
    "A League":              ("https://www.pinnacle.com/es/soccer/australia-a-league/matchups/",                "https://www.oddsportal.com/football/australia/a-league/",                              "https://www.oddschecker.com/es/futbol/australia/a-league/"),
    "Arabia Pro League":     ("https://www.pinnacle.com/es/soccer/saudi-arabia-pro-league/matchups/",           "https://www.oddsportal.com/football/saudi-arabia/saudi-professional-league/",          "https://www.oddschecker.com/es/futbol/arabia-saudi/saudi-pro-league/"),
    "Chinese Super League":  ("https://www.pinnacle.com/es/soccer/china-super-league/matchups/",                "https://www.oddsportal.com/football/china/super-league/",                              "https://www.oddschecker.com/es/futbol/china/superliga/"),
    "J League":              ("https://www.pinnacle.com/es/soccer/japan-j-league/matchups/",                    "https://www.oddsportal.com/football/japan/j1-league/",                                 "https://www.oddschecker.com/es/futbol/japon/j-league/"),
    "K League":              ("https://www.pinnacle.com/es/soccer/korea-republic-k-league-1/matchups/",         "https://www.oddsportal.com/football/south-korea/k-league-1/"),

    # ── Domestic cups ────────────────────────────────────────────────────────
    "Copa del Rey":          ("https://www.pinnacle.com/es/soccer/spain-copa-del-rey/matchups/",                "https://www.oddsportal.com/football/spain/copa-del-rey/",                              "https://www.oddschecker.com/es/futbol/espana/copa-del-rey/"),
    "Coupe de France":       ("https://www.pinnacle.com/es/soccer/france-cup/matchups/",                        "https://www.oddsportal.com/football/france/coupe-de-france/",                          "https://www.oddschecker.com/es/futbol/francia/coupe-de-france/"),
    "Coppa Italia":          ("https://www.pinnacle.com/es/soccer/italy-cup/matchups/",                         "https://www.oddsportal.com/football/italy/coppa-italia/",                              "https://www.oddschecker.com/es/futbol/italia/coppa-italia/"),
    "DFB Pokal":             ("https://www.pinnacle.com/es/soccer/germany-cup/matchups/",                       "https://www.oddsportal.com/football/germany/dfb-pokal/",                               "https://www.oddschecker.com/es/futbol/alemania/dfb-pokal/"),
    "FA Cup":                ("https://www.pinnacle.com/es/soccer/england-fa-cup/matchups/",                    "https://www.oddsportal.com/football/england/fa-cup/",                                  "https://www.oddschecker.com/es/futbol/inglaterra/fa-cup/"),
    "Kings Cup":             ("https://www.pinnacle.com/es/soccer/saudi-arabia-kings-cup/matchups/",            "https://www.oddsportal.com/football/saudi-arabia/king-cup/"),

    # ── Continental ──────────────────────────────────────────────────────────
    "Champions League":      ("https://www.pinnacle.com/es/soccer/uefa-champions-league/matchups/",             "https://www.oddsportal.com/football/europe/champions-league/",                         "https://www.oddschecker.com/es/futbol/competiciones/champions-league"),
    "Concacaf":              ("https://www.pinnacle.com/es/soccer/concacaf-champions-cup/matchups/",            "https://www.oddsportal.com/football/north-central-america/concacaf-champions-cup/",    "https://www.oddschecker.com/es/futbol/competiciones/liga-de-campeones-concacaf"),
    "Conference League":     ("https://www.pinnacle.com/es/soccer/uefa-conference-league/matchups/",            "https://www.oddsportal.com/football/europe/conference-league/",                        "https://www.oddschecker.com/es/futbol/competiciones/conference-league"),
    "Copa Libertadores":     ("https://www.pinnacle.com/es/soccer/conmebol-copa-libertadores/matchups/",        "https://www.oddsportal.com/football/south-america/copa-libertadores/",                 "https://www.oddschecker.com/es/futbol/internacional/copa-libertadores"),
    "Copa Sudamericana":     ("https://www.pinnacle.com/es/soccer/conmebol-copa-sudamericana/matchups/",        "https://www.oddsportal.com/football/south-america/copa-sudamericana/",                 "https://www.oddschecker.com/es/futbol/competiciones/copa-sudamericana"),
    "Europa League":         ("https://www.pinnacle.com/es/soccer/uefa-europa-league/matchups/",                "https://www.oddsportal.com/football/europe/europa-league/",                            "https://www.oddschecker.com/es/futbol/competiciones/europa-league"),
}
# fmt: on


# ── Category registry ─────────────────────────────────────────────────────────

CATEGORIES: dict[str, dict] = {
    "league_europe": {
        "label": "Ligas nacionales — Europa",
        "competitions": [
            "Austrian Bundesliga", "Belgium Pro League", "Bundesliga",
            "Czech First League", "Danish Superliga", "Eredivisie",
            "Greek Super League", "La Liga", "Ligue 1", "Norway Eliteserien",
            "Poland Ekstraklasa", "Premier League", "Primeira Liga",
            "Romanian Liga 1", "Russia Premier League", "Scottish Premiership",
            "Serie A", "Super Lig", "Swedish Allsvenskan", "Swiss Super League",
        ],
    },
    "league_americas": {
        "label": "Ligas nacionales — Américas",
        "competitions": [
            "Argentina Liga Pro", "Brasileirao", "Liga AUF",
            "Liga de Primera", "Liga MX", "MLS", "Primera A",
        ],
    },
    "league_asia": {
        "label": "Ligas nacionales — Asia / Oceanía",
        "competitions": [
            "A League", "Arabia Pro League", "Chinese Super League",
            "J League", "K League",
        ],
    },
    "domestic_cup": {
        "label": "Copas domésticas",
        "competitions": [
            "Copa del Rey", "Coupe de France", "Coppa Italia",
            "DFB Pokal", "FA Cup", "Kings Cup",
        ],
    },
    "continental": {
        "label": "Competiciones continentales",
        "competitions": [
            "Champions League", "Concacaf", "Conference League", "Copa Libertadores",
            "Copa Sudamericana", "Europa League",
        ],
    },
}

CATEGORIES["leagues"] = {
    "label": "Todas las ligas nacionales",
    "competitions": (
        CATEGORIES["league_europe"]["competitions"]
        + CATEGORIES["league_americas"]["competitions"]
        + CATEGORIES["league_asia"]["competitions"]
    ),
}


def competitions_by_category(category: str) -> list[str]:
    """Return the list of competition names for a given category slug."""
    if category not in CATEGORIES:
        valid = ", ".join(sorted(CATEGORIES))
        raise ValueError(f"Unknown category {category!r}. Valid options: {valid}")
    return list(CATEGORIES[category]["competitions"])


def resolve_targets(
    competitions: Optional[list[str]],
    categories: Optional[list[str]],
) -> list[str]:
    """
    Resolve the final list of competition names to scrape:
      1. If competitions is given, use those names directly.
      2. If categories is given, expand each and deduplicate.
      3. If neither, use all competitions.
    """
    if competitions:
        return competitions

    if categories:
        seen: set[str] = set()
        targets: list[str] = []
        for cat in categories:
            for name in competitions_by_category(cat):
                if name not in seen:
                    seen.add(name)
                    targets.append(name)
        return targets

    return list(COMPETITIONS.keys())
