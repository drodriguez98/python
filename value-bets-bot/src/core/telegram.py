"""
telegram.py
Telegram notification helpers: message formatting and delivery.
"""
from __future__ import annotations

import logging
import os
from datetime import date

import requests

from src.core.models import ValueBet

log = logging.getLogger(__name__)

_TELEGRAM_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN", "")
_TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def build_telegram_messages(bets: list[ValueBet]) -> list[str]:
    """Build one Telegram message per value bet."""
    messages = []
    for b in bets:
        hora  = b.kickoff.split("T")[1] if "T" in b.kickoff else ""
        emoji = "🔥" if b.value >= 0.05 else "✅"
        kelly_line = (
            f"📐 Kelly: <b>{b.kelly_fraction:.1%}</b> bankroll "
            f"(½Kelly: {b.kelly_fraction_half:.1%})\n"
            if b.kelly_fraction > 0 else ""
        )
        messages.append(
            f"{emoji} <b>{b.home_team} - {b.away_team}</b>\n"
            f"🏆 {b.competition} · {hora}\n"
            f"📋 Mercado: {b.market.upper()} → {b.outcome.upper()}\n"
            f"📌 Pinnacle: {b.pinnacle_odds:.2f} (prob real: {b.pinnacle_prob:.1%})\n"
            f"💰 Bet365: <b>{b.bet365_odds:.2f}</b> (prob impl: {b.implied_prob:.1%})\n"
            f"📈 EV: <b>{b.value:+.1%}</b>\n"
            f"{kelly_line}"
        )
    return messages


def telegram_send(text: str) -> bool:
    """Send a Telegram message. Silently skips if credentials are not configured."""
    if not _TELEGRAM_TOKEN or not _TELEGRAM_CHAT_ID:
        log.debug("[Telegram] Not configured, skipping notification.")
        return False
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{_TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": _TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        if not resp.ok:
            log.warning(f"[Telegram] Error {resp.status_code}: {resp.text[:100]}")
            return False
        log.info("[Telegram] Message sent.")
        return True
    except Exception as e:
        log.warning(f"[Telegram] Exception: {e}")
        return False


def telegram_send_bets(bets: list[ValueBet]) -> None:
    """Send one Telegram message per value bet."""
    for msg in build_telegram_messages(bets):
        telegram_send(msg)
