"""
team_aliases.py
Team name normalisation data: common suffixes to strip and manual aliases
for teams whose names differ between Pinnacle and OddsPortal.

To add a new alias:
  1. Find the normalised form of the name that needs mapping (lowercase, no
     diacritics, punctuation replaced by spaces, suffixes stripped).
  2. Add an entry: "variant_normalised": "canonical_normalised"
  Both sides must already be normalised (run _normalize() mentally first).

To add a new suffix:
  Extend SUFFIXES_PATTERN — use lowercase, whole-word tokens only.
"""

import re

# ── Common club suffixes to strip before comparison ───────────────────────────

SUFFIXES_PATTERN: re.Pattern = re.compile(
    r'\b(sc|fc|cf|ac|as|cd|ud|sd|rc|rcd|cp|if|bk|sk|fk|nk|ok|utd|united)\b'
)

# ── Manual aliases ─────────────────────────────────────────────────────────────
# Format: "normalised_variant" → "normalised_canonical"
# Both sides must be lowercase, diacritic-free, punctuation-free, suffix-free.

ALIASES: dict[str, str] = {
    # ── Arabia ──────────────────────────────────────────────────────────────────
    "al quadisiya":              "al qadsiah",
    "al qadsiah":                "al qadsiah",
    "al akhdoud":                "al okhdood",

    # ── Argentina Liga Pro ───────────────────────────────────────────────────────
    "gimnasia la plata":         "gimnasia",
    "gimnasia lp":               "gimnasia",
    "independiente rivadavia":   "ind rivadavia",
    "ind rivadavia":             "ind rivadavia",

    # ── Belgium Pro League ───────────────────────────────────────────────────────
    "royale union sg":           "union saint gilloise",
    "sint truidense":            "st truiden",
    "st truiden":                "st truiden",
    "royal antwerp":             "antwerp",
    "standard liege":            "st liege",
    "st liege":                  "st liege",
    "kv mechelen":               "mechelen",
    "cercle brugge ksv":         "cercle brugge",
    "raal la louviere":          "raal",

    # ── Brasileirao ──────────────────────────────────────────────────────────────
    "botafogo fr rj":            "botafogo",
    "botafogo rj":               "botafogo",
    "flamengo rj":               "flamengo",
    "athletico paranaense":      "athletico pr",
    "athletico pr":              "athletico pr",

    # ── Bundesliga ───────────────────────────────────────────────────────────────
    "borussia monchengladbach":  "mgladbach",
    "m gladbach":                "mgladbach",
    "b monchengladbach":         "mgladbach",

    # ── Danish Superliga ─────────────────────────────────────────────────────────
    "agf":                       "aarhus",
    "aarhus":                    "aarhus",
    "odense bk":                 "odense",
    "fc nordsjaelland":          "nordsjaelland",

    # ── Eredivisie ───────────────────────────────────────────────────────────────
    "pec zwolle":                "zwolle",
    "fc twente":                 "twente",
    "fc utrecht":                "utrecht",
    "az alkmaar":                "az",
    "alkmaar":                   "az",
    "heracles almelo":           "heracles",
    "go ahead eagles":           "ga eagles",
    "ga eagles":                 "ga eagles",

    # ── La Liga ──────────────────────────────────────────────────────────────────
    "athletic bilbao":           "ath bilbao",
    "atletico madrid":           "atl madrid",

    # ── Ligue 1 ──────────────────────────────────────────────────────────────────
    "paris saint germain":       "psg",
    "psg":                       "psg",

    # ── Liga de Primera (Chile) ──────────────────────────────────────────────────
    "u de chile":                "universidad de chile",
    "universidad catolica":      "u catolica",
    "u catolica":                "u catolica",
    "universidad de concepcion": "u de concepcion",
    "u de concepcion":           "u de concepcion",
    "everton vina del mar":      "everton",
    "deportes limache":          "limache",

    # ── MLS ──────────────────────────────────────────────────────────────────────
    "atlanta utd":               "atlanta",
    "atlanta united":            "atlanta",

    # ── Primera A (Colombia) ─────────────────────────────────────────────────────
    "international de bogota":   "inter bogota",
    "inter bogota":              "inter bogota",
    "atletico bucaramanga":      "bucaramanga",
    "cucuta deportivo":          "cucuta",
    "deportivo cali":            "dep cali",
    "deportivo pasto":           "dep pasto",
    "boyaca chico":              "chico",
    "independiente medellin":    "ind medellin",
    "ind medellin":              "ind medellin",

    # ── Premier League ───────────────────────────────────────────────────────────
    "manchester united":         "manchester",
    "manchester utd":            "manchester",
    "nottingham forest":         "nottingham",
    "tottenham hotspur":         "tottenham",
    "leeds united":              "leeds",
    "wolverhampton":             "wolves",
    "wolverhampton wanderers":   "wolves",

    # ── Russia Premier League ────────────────────────────────────────────────────
    "nizhny novgorod":           "pari nn",
    "pari nn":                   "pari nn",
    "krylia sovetov":            "krylya sovetov",
    "krylya sovetov":            "krylya sovetov",

    # ── Scottish Premiership ─────────────────────────────────────────────────────
    "dundee united":             "dundee utd",
    "dundee utd":                "dundee utd",

    # ── Serie A ──────────────────────────────────────────────────────────────────
    "internazionale":            "inter",

    # ── UEFA / Europa (Pinnacle usa locale es-ES → nombres de ciudad en español) ─
    # Praga / Prague
    "sparta praga":              "sparta prague",
    "sparta prague":             "sparta prague",
    "slavia praga":              "slavia prague",
    "slavia prague":             "slavia prague",
    "bohemians praga":           "bohemians prague",
    "dukla praga":               "dukla prague",
    # Colonia / Cologne
    "colonia":                   "cologne",
    "cologne":                   "cologne",
    # Moscú / Moscow
    "spartak moscu":             "spartak moscow",
    "spartak moscow":            "spartak moscow",
    "cska moscu":                "cska moscow",
    "cska moscow":               "cska moscow",
    "dinamo moscu":              "dinamo moscow",
    "lokomotiv moscu":           "lokomotiv moscow",
    # Varsovia / Warsaw
    "legia varsovia":            "legia warsaw",
    "legia warsaw":              "legia warsaw",
    # Ginebra / Geneva
    "servette ginebra":          "servette geneva",
    "servette":                  "servette",
}
