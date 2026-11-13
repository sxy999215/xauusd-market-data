# xauusd-market-data

Gold spot (XAU/USD) K-line data for the Chan/MACD/smart-money model.
Source: Jinrong China (GOLD 1-minute bars, decrypted from the app API).

## Files

| File | Rows | Content |
|---|---|---|
| data/xauusd_1m.csv | ~20,000 | Full 1-minute series (over 1 MB: use the weekly shards below for API reads) |
| data/xauusd_5m.csv | ~4,000 | Aggregated from 1m |
| data/xauusd_1h.csv | ~330 | Aggregated from 1m |
| data/xauusd_1d.csv | ~20 | Daily bars aggregated from real 1m (UTC calendar days) |
| data/1m/2026-W??.csv | ~7,000 each | 1-minute bars split by ISO week, each under 500 KB |
| data/raw/YYYY-MM-DD.json | ~1,400 each | Original decoded 1-minute bars split by UTC date, each under 500 KB |
| data/jinrong_raw.json | ~20,000 bars | Original Jinrong response (decoded 1m bars) |
| data/manifest.json | — | File paths, bar counts, start/end times, update time |
| UPDATE_LOG.md | — | Latest K-line time, bar counts and update time per update |

Columns: `datetime_utc,open,high,low,close,vol` (UTC, 2 decimals).
Aggregation uses UTC clock boundaries; volume is summed. Daily bars use
UTC calendar days (00:00-23:59 UTC); Sunday bars cover only the evening
session (market opens Sunday ~22:00 UTC).

Note: GitHub's Contents API returns no content for files over 1 MB, so the
full 1-minute CSV and the raw JSON are split into shards under 500 KB each.
Read `data/manifest.json` first to find the shard covering the dates needed.

## Updates

Hourly, incremental: each run pulls only the last 2 hours and merges by
timestamp (dedup), so history is never re-downloaded. The files pushed here
are always the full series; the last 1-minute bar may still be forming and
is overwritten by the completed bar on the next run. See UPDATE_LOG.md for
the latest update.
