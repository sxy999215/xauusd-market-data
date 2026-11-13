# xauusd-market-data

Gold spot (XAU/USD) K-line data for the Chan/MACD/smart-money model.
Source: Jinrong China (GOLD 1-minute bars, decrypted from the app API).

## Files

| File | Rows | Content |
|---|---|---|
| data/xauusd_1m.csv | ~20,000 | Full 1-minute series |
| data/xauusd_5m.csv | ~4,000 | Aggregated from 1m |
| data/xauusd_1h.csv | ~330 | Aggregated from 1m |
| data/jinrong_raw.json | ~20,000 bars | Original Jinrong response (decoded 1m bars) |
| UPDATE_LOG.md | — | Latest K-line time, bar counts and update time per update |

Columns: `datetime_utc,open,high,low,close,vol` (UTC, 2 decimals).
Aggregation uses UTC clock boundaries; volume is summed.

## Updates

Hourly, incremental: each run pulls only the last 2 hours and merges by
timestamp (dedup), so history is never re-downloaded. The files pushed here
are always the full series; the last 1-minute bar may still be forming and
is overwritten by the completed bar on the next run. See UPDATE_LOG.md for
the latest update.
