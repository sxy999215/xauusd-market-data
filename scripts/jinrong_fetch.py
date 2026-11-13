#!/usr/bin/env python3
"""Jinrong (金荣) 1-minute XAUUSD fetch.

Known request shape (from data/jinrong_raw.json in the repo):
    {"symbol": "GOLD", "periodType": 1, "start": <epoch>, "end": <epoch>}
with start/end spanning the last 2 hours. The response is
{"errcode": "0", "msg": "success", "data": "<base64 encrypted payload>"}
plus two small calls (pre_day / openPrice) with the same envelope.

NOT YET WIRED (2026-11-13): the API host and the payload decryption live
only in the updater script currently run by hand. Do NOT guess them here.
To wire this module, replace fetch_new_bars() with the real implementation
from that script. It must return:
    {"bars": [{"time": int, "open": float, "high": float, "low": float,
               "close": float, "vol": float}, ...]}
Bars must be 1-minute, UTC, ascending by time. The last bar may still be
forming; update.py overwrites same-timestamp bars on the next run.
(The repo no longer archives the raw Jinrong envelope: jinrong_raw.json was
removed as redundant on 2026-11-13, clean bars live in CSVs/shards.)
"""

WINDOW_SECONDS = 2 * 3600


class FetchNotWired(RuntimeError):
    """Raised until the Jinrong endpoint + decryption are wired in."""


def fetch_new_bars():
    """Fetch the last 2 hours of Jinrong 1-minute GOLD bars."""
    raise FetchNotWired(
        "Jinrong fetch not wired yet: the API host and payload decryption "
        "are only in the hand-run updater script. Paste that script's "
        "fetch+decrypt into this function, keeping the return shape above."
    )
